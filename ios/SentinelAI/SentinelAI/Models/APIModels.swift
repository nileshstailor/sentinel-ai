import Foundation

struct HomeSummaryDTO: Codable, Sendable {
    let userId: String
    let protectionStatus: String
    let lastGps: GpsEventDTO?
    let bankStatus: String
    let bankRestricted: Bool
    let verifiedCount: Int?
    let needsReviewCount: Int?
    let frozenCount: Int?
    let reviewedCount: Int
    let suspiciousCount: Int
    let urgentIncidents: Int
    let recentActions: [[String: AnyCodable]]
    let demoLabels: [String]
    let integrations: [String: String]
    let locationStatus: String?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case protectionStatus = "protection_status"
        case lastGps = "last_gps"
        case bankStatus = "bank_status"
        case bankRestricted = "bank_restricted"
        case verifiedCount = "verified_count"
        case needsReviewCount = "needs_review_count"
        case frozenCount = "frozen_count"
        case reviewedCount = "reviewed_count"
        case suspiciousCount = "suspicious_count"
        case urgentIncidents = "urgent_incidents"
        case recentActions = "recent_actions"
        case demoLabels = "demo_labels"
        case integrations
        case locationStatus = "location_status"
    }

    var verified: Int { verifiedCount ?? reviewedCount }
    var needsReview: Int { needsReviewCount ?? suspiciousCount }
    var frozen: Int { frozenCount ?? urgentIncidents }
}

struct GpsEventDTO: Codable, Identifiable, Sendable {
    var id: String { eventId }
    let eventId: String
    let userId: String
    let deviceId: String
    let eventTimestamp: String
    let lat: Double
    let lon: Double
    let horizontalAccuracyM: Double
    let source: String
    let receivedAt: String?
    let synthetic: Bool

    enum CodingKeys: String, CodingKey {
        case eventId = "event_id"
        case userId = "user_id"
        case deviceId = "device_id"
        case eventTimestamp = "event_timestamp"
        case lat, lon, source, synthetic
        case horizontalAccuracyM = "horizontal_accuracy_m"
        case receivedAt = "received_at"
    }
}

struct GpsListResponse: Codable, Sendable {
    let mode: String
    let count: Int
    let events: [GpsEventDTO]
}

struct GpsStoreResponse: Codable, Sendable {
    let stored: Bool
    let mode: String
    let event: GpsEventDTO
}

struct CustomerActionDTO: Codable, Sendable, Identifiable {
    var id: String { actionId }
    let actionId: String
    let label: String

    enum CodingKeys: String, CodingKey {
        case actionId = "id"
        case label
    }
}

struct IncidentDTO: Codable, Identifiable, Sendable {
    var id: String { incidentId }
    let incidentId: String
    let userId: String
    let title: String
    let scenario: String?
    let status: String
    let severity: String
    let customerStatus: String?
    let customerSummary: String?
    let customerAction: String?
    let customerFindings: [String]?
    let availableActions: [CustomerActionDTO]?
    let customerWhen: String?
    let reference: String?
    let conclusionSummary: String?
    let responseLevel: Int?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case incidentId = "incident_id"
        case userId = "user_id"
        case title, scenario, status, severity
        case customerStatus = "customer_status"
        case customerSummary = "customer_summary"
        case customerAction = "customer_action"
        case customerFindings = "customer_findings"
        case availableActions = "available_actions"
        case customerWhen = "customer_when"
        case reference
        case conclusionSummary = "conclusion_summary"
        case responseLevel = "response_level"
        case createdAt = "created_at"
    }

    var displayStatus: String { customerStatus ?? "Open" }
    var displaySummary: String {
        if let customerSummary, !customerSummary.isEmpty { return customerSummary }
        return conclusionSummary ?? "Sentinel reviewed this activity."
    }
    var displayWhen: String { customerWhen ?? reference ?? "Recent alert" }
    var findings: [String] { customerFindings ?? [] }
    var actions: [CustomerActionDTO] { availableActions ?? [] }
}

struct IncidentsResponse: Codable, Sendable {
    let count: Int
    let incidents: [IncidentDTO]
}

struct TransactionDTO: Codable, Identifiable, Sendable {
    var id: String { eventId }
    let eventId: String
    let merchant: String
    let amount: Double
    let currency: String
    let channel: String
    let postingTime: String
    let synthetic: Bool

    enum CodingKeys: String, CodingKey {
        case eventId = "event_id"
        case merchant, amount, currency, channel, synthetic
        case postingTime = "posting_time"
    }
}

struct TransactionsResponse: Codable, Sendable {
    let synthetic: Bool
    let count: Int
    let events: [TransactionDTO]
    let label: String
}

struct BankStatusDTO: Codable, Sendable {
    let restricted: Bool?
    let balance: Double?
    let restrictionReason: String?
    let demoLabel: String?

    enum CodingKeys: String, CodingKey {
        case restricted, balance
        case restrictionReason = "restriction_reason"
        case demoLabel = "demo_label"
    }
}

struct TransferResultDTO: Codable, Sendable {
    let success: Bool
    let status: String
    let message: String
    let restricted: Bool?
    let demoLabel: String?

    enum CodingKeys: String, CodingKey {
        case success, status, message, restricted
        case demoLabel = "demo_label"
    }

    var isBlocked: Bool {
        !success || status == "rejected_restricted" || restricted == true
    }
}

enum AnyCodable: Codable, Sendable {
    case null
    case bool(Bool)
    case int(Int)
    case double(Double)
    case string(String)
    case array([AnyCodable])
    case object([String: AnyCodable])

    var value: Any {
        switch self {
        case .null: return NSNull()
        case .bool(let v): return v
        case .int(let v): return v
        case .double(let v): return v
        case .string(let v): return v
        case .array(let v): return v.map(\.value)
        case .object(let v): return v.mapValues(\.value)
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() { self = .null }
        else if let b = try? container.decode(Bool.self) { self = .bool(b) }
        else if let i = try? container.decode(Int.self) { self = .int(i) }
        else if let d = try? container.decode(Double.self) { self = .double(d) }
        else if let s = try? container.decode(String.self) { self = .string(s) }
        else if let arr = try? container.decode([AnyCodable].self) { self = .array(arr) }
        else if let dict = try? container.decode([String: AnyCodable].self) { self = .object(dict) }
        else { self = .null }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .null: try container.encodeNil()
        case .bool(let v): try container.encode(v)
        case .int(let v): try container.encode(v)
        case .double(let v): try container.encode(v)
        case .string(let v): try container.encode(v)
        case .array(let v): try container.encode(v)
        case .object(let v): try container.encode(v)
        }
    }
}
