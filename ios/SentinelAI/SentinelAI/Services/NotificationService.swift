import Foundation
import UserNotifications
import UIKit

@MainActor
final class NotificationService {
    static let shared = NotificationService()

    private let center = UNUserNotificationCenter.current()
    private let notifiedKey = "sentinel.notified.incident.ids"
    private var authorized = false

    private init() {}

    func requestPermission() async {
        do {
            authorized = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            await MainActor.run {
                UIApplication.shared.registerForRemoteNotifications()
            }
        } catch {
            authorized = false
        }
    }

    func notifyUrgent(title: String, body: String, incidentId: String) async {
        guard shouldNotify(incidentId: incidentId) else { return }
        if !authorized {
            await requestPermission()
        }
        guard authorized else { return }

        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        content.badge = 1
        content.interruptionLevel = .timeSensitive
        content.userInfo = ["incident_id": incidentId]

        let request = UNNotificationRequest(
            identifier: "urgent-\(incidentId)",
            content: content,
            trigger: nil
        )
        try? await center.add(request)
        markNotified(incidentId: incidentId)
    }

    func notifyTransferBlocked(message: String) async {
        if !authorized {
            await requestPermission()
        }
        guard authorized else { return }

        let content = UNMutableNotificationContent()
        content.title = "Transfer blocked"
        content.body = message
        content.sound = .default
        content.interruptionLevel = .timeSensitive

        let request = UNNotificationRequest(
            identifier: "transfer-blocked-\(UUID().uuidString)",
            content: content,
            trigger: nil
        )
        try? await center.add(request)
    }

    func clearBadge() {
        Task {
            try? await center.setBadgeCount(0)
        }
    }

    private func shouldNotify(incidentId: String) -> Bool {
        !notifiedIds().contains(incidentId)
    }

    private func markNotified(incidentId: String) {
        var ids = notifiedIds()
        ids.insert(incidentId)
        UserDefaults.standard.set(Array(ids), forKey: notifiedKey)
    }

    private func notifiedIds() -> Set<String> {
        Set(UserDefaults.standard.stringArray(forKey: notifiedKey) ?? [])
    }

    func resetNotifiedCache() {
        UserDefaults.standard.removeObject(forKey: notifiedKey)
    }
}
