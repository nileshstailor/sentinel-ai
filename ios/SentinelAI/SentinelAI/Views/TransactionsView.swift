import SwiftUI

struct TransactionsView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        NavigationStack {
            List(model.transactions) { txn in
                let status = statusFor(txn)
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(txn.merchant).font(.headline)
                        Spacer()
                        Text(String(format: "$%.2f", txn.amount))
                            .font(.body.weight(.semibold))
                    }
                    HStack {
                        Text(status.label)
                            .font(.caption.weight(.bold))
                            .foregroundStyle(status.color)
                        Spacer()
                        Text(txn.channel.replacingOccurrences(of: "_", with: " ").capitalized)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 2)
            }
            .navigationTitle("Activity")
            .overlay {
                if model.transactions.isEmpty {
                    ContentUnavailableView(
                        "No activity yet",
                        systemImage: "creditcard",
                        description: Text("Charges appear when you run a scenario in Demo Lab.")
                    )
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Refresh") { Task { await model.refreshAll() } }
                }
            }
            .task { await model.refreshAll() }
        }
    }

    private func statusFor(_ txn: TransactionDTO) -> (label: String, color: Color) {
        // Match related incidents by merchant keywords when possible
        let merchant = txn.merchant.lowercased()
        if let hit = model.incidents.first(where: { incident in
            let blob = (incident.title + " " + incident.displaySummary).lowercased()
            return merchant.split(separator: " ").prefix(2).contains { blob.contains($0) }
                || blob.contains("restaurant") && merchant.contains("restaurant")
                || blob.contains("takeover") && merchant.contains("transfer")
        }) {
            return (hit.displayStatus, colorFor(hit.displayStatus))
        }
        return ("Reviewed", Color(red: 0.45, green: 0.95, blue: 0.82))
    }

    private func colorFor(_ status: String) -> Color {
        switch status {
        case "Verified": return Color(red: 0.45, green: 0.95, blue: 0.82)
        case "Needs review": return .orange
        case "Account protected": return .red
        default: return .secondary
        }
    }
}
