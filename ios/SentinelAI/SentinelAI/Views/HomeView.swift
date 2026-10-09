import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.05, green: 0.08, blue: 0.12),
                        Color(red: 0.08, green: 0.14, blue: 0.18),
                        Color(red: 0.04, green: 0.06, blue: 0.09)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("SENTINEL AI")
                                .font(.system(size: 34, weight: .bold, design: .rounded))
                                .foregroundStyle(
                                    LinearGradient(
                                        colors: [
                                            Color(red: 0.45, green: 0.95, blue: 0.82),
                                            Color(red: 0.7, green: 0.9, blue: 1.0)
                                        ],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                            Text("Your money has a bodyguard.")
                                .font(.system(.title3, design: .serif))
                                .foregroundStyle(.secondary)
                        }
                        .padding(.top, 8)

                        simpleCard(
                            title: "Protection",
                            value: model.home?.protectionStatus == "On" ? "On" : (model.home?.protectionStatus ?? "…"),
                            detail: model.home?.bankRestricted == true
                                ? "Your account is frozen after a high-risk alert."
                                : "Quietly watching for unusual activity."
                        )

                        simpleCard(
                            title: "Your location",
                            value: model.home?.locationStatus ?? (model.home?.lastGps != nil ? "Location on" : "…"),
                            detail: model.home?.lastGps != nil
                                ? "Updated recently. Used only to verify purchases."
                                : "Open Location to share GPS for purchase checks."
                        )

                        simpleCard(
                            title: "Bank account",
                            value: model.home?.bankStatus ?? "…",
                            detail: model.home?.bankRestricted == true
                                ? "Transfers are blocked. Open an alert to unfreeze, or reset from Demo Lab."
                                : "Sentinel is watching for unusual transfers and card activity.",
                            emphasize: model.home?.bankRestricted == true
                        )

                        HStack(spacing: 12) {
                            metric("Verified", value: model.home?.verified ?? 0, tint: Color(red: 0.45, green: 0.95, blue: 0.82))
                            metric("Needs review", value: model.home?.needsReview ?? 0, tint: .orange)
                            metric("Frozen", value: model.home?.frozen ?? 0, tint: .red)
                        }

                        if model.bank?.restricted == true || model.home?.bankRestricted == true {
                            simpleCard(
                                title: "Urgent",
                                value: "Account protected",
                                detail: "A high-risk alert froze your account. Open Alerts, or prove it in Demo Lab with Attempt transfer.",
                                emphasize: true
                            )
                        }

                        if !model.statusMessage.isEmpty && model.statusMessage != "Ready" {
                            Text(model.statusMessage)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        if let err = model.lastError {
                            Text(err).font(.caption).foregroundStyle(.orange)
                        }
                    }
                    .padding()
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await model.refreshAll() }
                    } label: {
                        if model.isBusy {
                            ProgressView()
                        } else {
                            Text("Refresh")
                        }
                    }
                    .disabled(model.isBusy)
                }
            }
        }
    }

    private func simpleCard(title: String, value: String, detail: String, emphasize: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.title3.weight(.semibold))
                .foregroundStyle(emphasize ? Color.orange : Color.primary)
            Text(detail)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
    }

    private func metric(_ title: String, value: Int, tint: Color) -> some View {
        VStack(spacing: 4) {
            Text("\(value)").font(.title.weight(.bold)).foregroundStyle(tint)
            Text(title).font(.caption2).foregroundStyle(.secondary).multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 14)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 14))
    }
}
