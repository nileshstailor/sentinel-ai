import SwiftUI

struct IncidentsView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        NavigationStack {
            List(model.incidents) { incident in
                NavigationLink {
                    IncidentDetailView(incidentId: incident.incidentId)
                } label: {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack(alignment: .top) {
                            Text(incident.title)
                                .font(.headline)
                                .fixedSize(horizontal: false, vertical: true)
                            Spacer(minLength: 8)
                            statusChip(incident.displayStatus)
                        }
                        Text(incident.displayWhen)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text(incident.displaySummary)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .padding(.vertical, 4)
                }
            }
            .navigationTitle("Alerts")
            .overlay {
                if model.incidents.isEmpty {
                    ContentUnavailableView(
                        "All clear",
                        systemImage: "checkmark.shield",
                        description: Text("No alerts right now.")
                    )
                }
            }
            .task { await model.refreshAll() }
        }
    }

    private func statusChip(_ status: String) -> some View {
        Text(status)
            .font(.caption2.weight(.bold))
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(chipColor(status).opacity(0.25), in: Capsule())
            .foregroundStyle(chipColor(status))
    }

    private func chipColor(_ status: String) -> Color {
        switch status {
        case "Verified": return Color(red: 0.45, green: 0.95, blue: 0.82)
        case "Needs review": return .orange
        case "Account protected": return .red
        default: return .secondary
        }
    }
}

struct IncidentDetailView: View {
    @EnvironmentObject private var model: AppModel
    let incidentId: String
    @State private var busyAction: String?

    private var incident: IncidentDTO? {
        model.incidents.first(where: { $0.incidentId == incidentId })
    }

    var body: some View {
        Group {
            if let incident {
                List {
                    Section {
                        Text(incident.displayStatus)
                            .font(.title3.weight(.semibold))
                        Text(incident.displayWhen)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text(incident.displaySummary)
                            .font(.body)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    if !incident.findings.isEmpty {
                        Section("What Sentinel found") {
                            ForEach(incident.findings, id: \.self) { finding in
                                Text(finding)
                                    .font(.body)
                                    .fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }

                    if !incident.actions.isEmpty {
                        Section("Choose what happens next") {
                            ForEach(incident.actions) { action in
                                Button {
                                    Task {
                                        busyAction = action.actionId
                                        await model.performIncidentAction(
                                            incidentId: incident.incidentId,
                                            actionId: action.actionId
                                        )
                                        busyAction = nil
                                    }
                                } label: {
                                    HStack {
                                        Text(action.label)
                                            .font(.body.weight(.semibold))
                                        Spacer()
                                        if busyAction == action.actionId || model.isBusy {
                                            ProgressView()
                                        } else {
                                            Image(systemName: "chevron.right")
                                                .font(.caption.weight(.semibold))
                                                .foregroundStyle(.secondary)
                                        }
                                    }
                                }
                                .disabled(busyAction != nil || model.isBusy)
                            }
                            Text("Freeze and unfreeze ask for Face ID so only you can change account protection.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .navigationTitle(incident.title)
                .navigationBarTitleDisplayMode(.inline)
            } else {
                ContentUnavailableView("Alert unavailable", systemImage: "bell.slash")
            }
        }
        .task { await model.refreshAll() }
    }
}
