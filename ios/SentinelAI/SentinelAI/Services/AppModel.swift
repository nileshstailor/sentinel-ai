import Foundation
import SwiftUI
import UIKit

struct ActionFeedback: Identifiable, Equatable {
    let id = UUID()
    let title: String
    let message: String
    let isSuccess: Bool
}

@MainActor
final class AppModel: ObservableObject {
    @Published var home: HomeSummaryDTO?
    @Published var incidents: [IncidentDTO] = []
    @Published var transactions: [TransactionDTO] = []
    @Published var gpsEvents: [GpsEventDTO] = []
    @Published var bank: BankStatusDTO?
    @Published var statusMessage: String = "Ready"
    @Published var lastError: String?
    @Published var apiBaseURL: String
    @Published var apiToken: String
    @Published var isBusy = false
    @Published var busyLabel: String = ""
    @Published var feedback: ActionFeedback?
    @Published var notificationsEnabled = false

    let location = LocationService()

    private static let defaultsURLKey = "sentinel.apiBaseURL"
    private static let defaultsTokenKey = "sentinel.apiToken"

    init() {
        let defaults = UserDefaults.standard
        let savedURL = defaults.string(forKey: Self.defaultsURLKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let savedToken = defaults.string(forKey: Self.defaultsTokenKey)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let local = Self.loadLocalConfig()
        let plist = Bundle.main
        let plistURL = (plist.object(forInfoDictionaryKey: "APIBaseURL") as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if let savedURL, !savedURL.isEmpty, !Self.isPlaceholder(savedURL) {
            apiBaseURL = savedURL
        } else if let localURL = local.url, !localURL.isEmpty, !Self.isPlaceholder(localURL) {
            apiBaseURL = localURL
        } else if let plistURL, !plistURL.isEmpty, !Self.isPlaceholder(plistURL) {
            apiBaseURL = plistURL
        } else {
            apiBaseURL = APIClient.defaultBaseURL
        }
        let plistToken = (plist.object(forInfoDictionaryKey: "APIToken") as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if let savedToken, !savedToken.isEmpty, !Self.isPlaceholder(savedToken) {
            apiToken = savedToken
        } else if let localToken = local.token, !localToken.isEmpty, !Self.isPlaceholder(localToken) {
            apiToken = localToken
        } else if let plistToken, !plistToken.isEmpty, !Self.isPlaceholder(plistToken) {
            apiToken = plistToken
        } else {
            apiToken = "dev-sentinel-token-change-me"
        }
    }

    private static func isPlaceholder(_ value: String) -> Bool {
        value.contains("REPLACE") || value.contains("change-me")
    }

    /// Optional untracked `Config.local.plist` in the app bundle (gitignored) for local demos.
    private static func loadLocalConfig() -> (url: String?, token: String?) {
        guard let url = Bundle.main.url(forResource: "Config.local", withExtension: "plist"),
              let dict = NSDictionary(contentsOf: url) as? [String: Any]
        else { return (nil, nil) }
        let base = (dict["APIBaseURL"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        let token = (dict["APIToken"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        return (base, token)
    }

    func bootstrap() async {
        await NotificationService.shared.requestPermission()
        notificationsEnabled = true
        await refreshAll()
    }

    func applyConfig() async {
        await APIClient.shared.configure(baseURL: apiBaseURL, token: apiToken)
        UserDefaults.standard.set(apiBaseURL, forKey: Self.defaultsURLKey)
        UserDefaults.standard.set(apiToken, forKey: Self.defaultsTokenKey)
        statusMessage = "API configured"
    }

    func refreshAll(preserveStatus: Bool = false) async {
        let previousStatus = statusMessage
        await applyConfig()
        do {
            home = try await APIClient.shared.home()
            let incidentResp = try await APIClient.shared.incidents()
            incidents = incidentResp.incidents
            let txnResp = try await APIClient.shared.transactions()
            transactions = txnResp.events
            let gpsResp = try await APIClient.shared.listGPS()
            gpsEvents = gpsResp.events
            bank = try await APIClient.shared.bankStatus()
            if preserveStatus {
                statusMessage = previousStatus
            } else {
                statusMessage = "Synced \(Date().formatted(date: .omitted, time: .standard))"
            }
            lastError = nil
            await notifyForUrgentIncidents()
            NotificationService.shared.clearBadge()
        } catch {
            lastError = error.localizedDescription
            presentFeedback(title: "Couldn’t sync", message: error.localizedDescription, success: false)
        }
    }

    func runScenario(_ name: String) async {
        guard beginBusy(label: "Running scenario…") else { return }
        defer { endBusy() }

        do {
            let result = try await APIClient.shared.runScenario(name)
            await refreshAll(preserveStatus: true)
            let title = Self.friendlyScenarioName(name)
            var message = Self.scenarioResultMessage(name: name, result: result, bank: bank)
            if name == "account_takeover" {
                message += "\n\nNext: tap “Attempt transfer after takeover” to prove the freeze."
                if let incident = incidents.first(where: { ($0.scenario ?? "").contains("takeover") || $0.displayStatus == "Account protected" }) {
                    await NotificationService.shared.notifyUrgent(
                        title: "Urgent · Account protected",
                        body: incident.displaySummary,
                        incidentId: incident.incidentId
                    )
                }
            } else if let top = incidents.first {
                if top.displayStatus == "Account protected" || top.displayStatus == "Needs review" {
                    await NotificationService.shared.notifyUrgent(
                        title: "\(top.displayStatus) · \(top.title)",
                        body: top.displaySummary,
                        incidentId: top.incidentId
                    )
                }
            }
            statusMessage = message
            lastError = nil
            presentFeedback(title: title, message: message, success: true)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        } catch {
            lastError = error.localizedDescription
            presentFeedback(title: "Scenario failed", message: error.localizedDescription, success: false)
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
    }

    func probeTransfer() async {
        guard beginBusy(label: "Attempting transfer…") else { return }
        defer { endBusy() }

        do {
            let result = try await APIClient.shared.transfer(
                amount: 25,
                recipient: "attacker-cashout@evil.example"
            )
            await refreshAll(preserveStatus: true)

            let blocked = result.isBlocked
            let title = blocked ? "Transfer blocked" : "Transfer went through"
            let message: String
            let apiNote = Self.sanitizeUserFacing(result.message)
            if blocked {
                message = """
                Sentinel stopped a $25 transfer to attacker-cashout@evil.example.

                \(apiNote)

                Account status: \(bank?.restricted == true ? "Frozen" : "Open")
                """
                await NotificationService.shared.notifyTransferBlocked(message: "Sentinel blocked a $25 transfer while your account is frozen.")
                UINotificationFeedbackGenerator().notificationOccurred(.warning)
            } else {
                message = """
                Transfer was not blocked. Run “Stolen phone — Freeze account” first, then try again.

                \(apiNote)
                """
                UINotificationFeedbackGenerator().notificationOccurred(.error)
            }
            statusMessage = title + " — " + result.status
            lastError = nil
            presentFeedback(title: title, message: message, success: blocked)
        } catch {
            lastError = error.localizedDescription
            presentFeedback(
                title: "Transfer check failed",
                message: error.localizedDescription,
                success: false
            )
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
    }

    func resetDemo() async {
        guard beginBusy(label: "Resetting demo…") else { return }
        defer { endBusy() }

        do {
            _ = try await APIClient.shared.resetDemo()
            NotificationService.shared.resetNotifiedCache()
            await refreshAll(preserveStatus: true)
            statusMessage = "Log cleared — account unfrozen"
            lastError = nil
            presentFeedback(
                title: "Reset complete",
                message: "Alerts cleared and your account is open again. GPS history was kept.",
                success: true
            )
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        } catch {
            lastError = error.localizedDescription
            presentFeedback(title: "Reset failed", message: error.localizedDescription, success: false)
        }
    }

    func performIncidentAction(incidentId: String, actionId: String) async {
        guard beginBusy(label: "Updating alert…") else { return }
        defer { endBusy() }

        // Face ID for protective account actions after a risky alert — not for Demo Lab buttons.
        if Self.requiresBiometric(actionId: actionId) {
            let reason = Self.biometricReason(actionId: actionId)
            let ok = await BiometricService.authenticate(reason: reason)
            guard ok else {
                lastError = "Face ID / Touch ID required"
                presentFeedback(
                    title: "Confirm it’s you",
                    message: "Sentinel needs Face ID or Touch ID before changing account protection.",
                    success: false
                )
                return
            }
        }

        do {
            _ = try await APIClient.shared.incidentAction(incidentId: incidentId, actionId: actionId)
            await refreshAll(preserveStatus: true)
            let label = incidents.first(where: { $0.incidentId == incidentId })?.displayStatus ?? "Updated"
            statusMessage = "Alert updated — \(label)"
            lastError = nil
            presentFeedback(title: "Done", message: "Alert is now: \(label).", success: true)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        } catch {
            lastError = error.localizedDescription
            presentFeedback(title: "Action failed", message: error.localizedDescription, success: false)
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
    }

    func runElevenLabsSOS() async {
        guard beginBusy(label: "Calling ElevenLabs…") else { return }
        defer { endBusy() }

        let ok = await BiometricService.authenticate(reason: "Confirm fraud hotline escalation")
        guard ok else {
            lastError = "Face ID / Touch ID required"
            presentFeedback(
                title: "Confirm it’s you",
                message: "Sentinel needs Face ID or Touch ID before escalating to the fraud hotline.",
                success: false
            )
            return
        }
        do {
            let result = try await APIClient.shared.elevenLabsSOS()
            let success = (result["success"]?.value as? Bool) ?? false
            let bytes = result["audio_bytes"]?.value as? Int ?? 0
            if success {
                statusMessage = "ElevenLabs fraud-hotline voice ready"
                lastError = nil
                presentFeedback(
                    title: "Fraud hotline voice ready",
                    message: """
                    After an account freeze, Sentinel can escalate by calling a fraud hotline as an AI assistant.

                    This button hits the live ElevenLabs API and generates that voice message (~\(max(bytes / 1024, 1)) KB of speech) — the sponsor stretch for “agent places the call.”
                    """,
                    success: true
                )
                UINotificationFeedbackGenerator().notificationOccurred(.success)
            } else {
                statusMessage = "ElevenLabs hotline failed"
                presentFeedback(
                    title: "Hotline voice failed",
                    message: "ElevenLabs did not return audio. Check the API key and try again.",
                    success: false
                )
            }
        } catch {
            lastError = error.localizedDescription
            presentFeedback(title: "Hotline voice failed", message: error.localizedDescription, success: false)
        }
    }

    func dismissFeedback() {
        feedback = nil
    }

    // MARK: - Private

    private func beginBusy(label: String) -> Bool {
        guard !isBusy else { return false }
        isBusy = true
        busyLabel = label
        statusMessage = label
        lastError = nil
        return true
    }

    private func endBusy() {
        isBusy = false
        busyLabel = ""
    }

    private func presentFeedback(title: String, message: String, success: Bool) {
        feedback = ActionFeedback(title: title, message: message, isSuccess: success)
    }

    private func notifyForUrgentIncidents() async {
        for incident in incidents where incident.displayStatus == "Account protected" {
            await NotificationService.shared.notifyUrgent(
                title: "Urgent · Account protected",
                body: incident.displaySummary,
                incidentId: incident.incidentId
            )
        }
        for incident in incidents where incident.displayStatus == "Needs review" {
            await NotificationService.shared.notifyUrgent(
                title: "Needs review · \(incident.title)",
                body: incident.displaySummary,
                incidentId: incident.incidentId
            )
        }
    }

    private static func requiresBiometric(actionId: String) -> Bool {
        ["freeze", "unfreeze", "keep_frozen"].contains(actionId)
    }

    private static func biometricReason(actionId: String) -> String {
        switch actionId {
        case "freeze":
            return "Confirm with Face ID to freeze your account"
        case "unfreeze":
            return "Confirm with Face ID to unfreeze your account"
        case "keep_frozen":
            return "Confirm with Face ID to keep your account frozen"
        default:
            return "Confirm with Face ID to change account protection"
        }
    }

    private static func sanitizeUserFacing(_ text: String) -> String {
        var out = text
        let junk = [
            " (SIMULATED)", "(SIMULATED)", "SIMULATED_BANK — not a real financial institution",
            "SIMULATED_BANK — protective freeze is demo-only", "SIMULATED_BANK",
            " — not a real financial institution", "demo-only", "simulated ", "Simulated ",
        ]
        for token in junk {
            out = out.replacingOccurrences(of: token, with: "")
        }
        return out
            .replacingOccurrences(of: "  ", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func friendlyScenarioName(_ name: String) -> String {
        switch name {
        case "restaurant_match": return "Restaurant — Should Verify"
        case "restaurant_insufficient": return "Restaurant — Needs Review"
        case "colombia_online": return "Online Colombia — Needs review"
        case "colombia_card_present": return "Risky Colombia card use"
        case "account_takeover": return "Stolen phone — Account frozen"
        default: return "Scenario complete"
        }
    }

    private static func scenarioResultMessage(
        name: String,
        result: [String: AnyCodable],
        bank: BankStatusDTO?
    ) -> String {
        var customerStatus = "Updated"
        if case let .object(inc)? = result["incident"] {
            if case let .string(s)? = inc["customer_status"] { customerStatus = s }
            else if case let .string(s)? = inc["status"] { customerStatus = s }
        }

        if name == "account_takeover" {
            var xferLine = "A follow-up attacker transfer was attempted."
            if case let .object(xfer)? = result["subsequent_transfer"] {
                if case let .string(st)? = xfer["status"] {
                    xferLine = st == "rejected_restricted"
                        ? "Follow-up transfer: blocked (account frozen)."
                        : "Follow-up transfer status: \(st)."
                }
            }
            let frozen = bank?.restricted == true
            return """
            Status: \(customerStatus)
            Account: \(frozen ? "Frozen" : "Open")
            \(xferLine)
            """
        }

        return "Status: \(customerStatus). Open Alerts to review."
    }
}
