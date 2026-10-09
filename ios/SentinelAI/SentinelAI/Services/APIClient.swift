import Foundation
import UIKit

enum APIError: LocalizedError {
    case invalidURL
    case http(Int, String)
    case decoding(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid API URL. Set APIBaseURL in Demo Lab to the AWS API Gateway URL."
        case .http(let code, let body): return "HTTP \(code): \(body)"
        case .decoding(let err): return "Decode error: \(err.localizedDescription)"
        }
    }
}

actor APIClient {
    static let shared = APIClient()

    static let defaultBaseURL = "https://8m6o4go9oc.execute-api.us-east-1.amazonaws.com/prod"

    private var baseURL: URL
    private var token: String
    private let session: URLSession

    init() {
        let plist = Bundle.main
        let urlString = (plist.object(forInfoDictionaryKey: "APIBaseURL") as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let resolved = (urlString?.isEmpty == false && !(urlString?.contains("REPLACE_AFTER_AWS_DEPLOY") ?? true))
            ? urlString!
            : Self.defaultBaseURL
        self.baseURL = URL(string: resolved) ?? URL(string: Self.defaultBaseURL)!
        let plistToken = (plist.object(forInfoDictionaryKey: "APIToken") as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        self.token = (plistToken?.isEmpty == false && plistToken != "$(SENTINEL_API_TOKEN)")
            ? plistToken!
            : "dev-sentinel-token-change-me"
        self.session = .shared
    }

    func configure(baseURL: String, token: String) {
        let trimmed = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        if let url = URL(string: trimmed), url.host != nil {
            self.baseURL = url
        }
        let t = token.trimmingCharacters(in: .whitespacesAndNewlines)
        if !t.isEmpty {
            self.token = t
        }
    }

    private func makeURL(path: String) throws -> URL {
        var base = baseURL.absoluteString
        while base.hasSuffix("/") { base.removeLast() }
        let suffix = path.hasPrefix("/") ? path : "/" + path
        guard let url = URL(string: base + suffix), url.host != nil else {
            throw APIError.invalidURL
        }
        return url
    }

    private func request<T: Decodable>(
        _ path: String,
        method: String = "GET",
        body: Data? = nil
    ) async throws -> T {
        let url = try makeURL(path: path)
        var req = URLRequest(url: url)
        req.httpMethod = method
        let deviceId = await MainActor.run {
            UIDevice.current.identifierForVendor?.uuidString ?? "demo-iphone-001"
        }
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.setValue("demo-user-001", forHTTPHeaderField: "X-Sentinel-User")
        req.setValue(deviceId, forHTTPHeaderField: "X-Sentinel-Device")
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = body

        let (data, response) = try await session.data(for: req)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.http(-1, "No response")
        }
        guard (200..<300).contains(http.statusCode) else {
            throw APIError.http(http.statusCode, String(data: data, encoding: .utf8) ?? "")
        }
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }

    func health() async throws -> [String: AnyCodable] {
        try await request("/health")
    }

    func home() async throws -> HomeSummaryDTO {
        try await request("/v1/home")
    }

    func uploadGPS(lat: Double, lon: Double, accuracy: Double, synthetic: Bool = false) async throws -> GpsStoreResponse {
        let payload: [String: Any] = [
            "lat": lat,
            "lon": lon,
            "horizontal_accuracy_m": accuracy,
            "event_timestamp": ISO8601DateFormatter().string(from: Date()),
            "source": "core_location",
            "synthetic": synthetic
        ]
        let data = try JSONSerialization.data(withJSONObject: payload)
        return try await request("/v1/gps", method: "POST", body: data)
    }

    func listGPS() async throws -> GpsListResponse {
        try await request("/v1/gps")
    }

    func incidents() async throws -> IncidentsResponse {
        try await request("/v1/incidents")
    }

    func transactions() async throws -> TransactionsResponse {
        try await request("/v1/transactions")
    }

    func bankStatus() async throws -> BankStatusDTO {
        try await request("/v1/bank/status")
    }

    func runScenario(_ name: String) async throws -> [String: AnyCodable] {
        try await request("/v1/demo/scenarios/\(name)", method: "POST")
    }

    func elevenLabsSOS() async throws -> [String: AnyCodable] {
        try await request("/v1/demo/elevenlabs-sos", method: "POST")
    }

    func resetDemo() async throws -> [String: AnyCodable] {
        try await request("/v1/demo/reset", method: "POST")
    }

    func incidentAction(incidentId: String, actionId: String) async throws -> [String: AnyCodable] {
        try await request("/v1/incidents/\(incidentId)/actions/\(actionId)", method: "POST")
    }

    func transfer(amount: Double, recipient: String) async throws -> TransferResultDTO {
        let payload: [String: Any] = [
            "account_id": "acct_demo_checking",
            "user_id": "demo-user-001",
            "amount": amount,
            "recipient": recipient
        ]
        let data = try JSONSerialization.data(withJSONObject: payload)
        return try await request("/v1/bank/transfer", method: "POST", body: data)
    }
}
