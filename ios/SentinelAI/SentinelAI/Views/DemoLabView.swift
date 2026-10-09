import SwiftUI

struct DemoLabView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        NavigationStack {
            Form {
                if model.isBusy {
                    Section {
                        HStack(spacing: 12) {
                            ProgressView()
                            Text(model.busyLabel.isEmpty ? "Working…" : model.busyLabel)
                                .font(.subheadline.weight(.medium))
                        }
                    }
                }

                Section("API endpoint") {
                    TextField("API Base URL", text: $model.apiBaseURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .font(.system(.footnote, design: .monospaced))
                        .disabled(model.isBusy)
                    SecureField("API Token", text: $model.apiToken)
                        .disabled(model.isBusy)
                    Button {
                        Task { await model.refreshAll() }
                    } label: {
                        Label("Save & Sync", systemImage: "arrow.triangle.2.circlepath")
                    }
                    .disabled(model.isBusy)
                }

                Section("Reset") {
                    Button(role: .destructive) {
                        Task { await model.resetDemo() }
                    } label: {
                        Label("Reset alerts & unfreeze", systemImage: "trash")
                    }
                    .disabled(model.isBusy)
                    Text("Clears alerts and unfreezes the account. Keeps your GPS history.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Try a scenario") {
                    scenarioButton("Restaurant charge — Should Verify", "restaurant_match")
                    scenarioButton("Restaurant charge — Needs Review", "restaurant_insufficient")
                    scenarioButton("Online Colombia purchase — Needs review", "colombia_online")
                    scenarioButton("Risky Colombia card use", "colombia_card_present")
                    scenarioButton("Stolen phone — Freeze account", "account_takeover")
                }

                Section("Prove restriction") {
                    Button {
                        Task { await model.probeTransfer() }
                    } label: {
                        HStack {
                            Label("Attempt transfer after takeover", systemImage: "arrow.left.arrow.right")
                            Spacer()
                            if model.isBusy && model.busyLabel.contains("transfer") {
                                ProgressView()
                            }
                        }
                    }
                    .disabled(model.isBusy)
                    Text("Run Stolen phone first. A frozen account should reject the transfer — you’ll see the result and get a notification.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("ElevenLabs · Fraud hotline") {
                    Button {
                        Task { await model.runElevenLabsSOS() }
                    } label: {
                        HStack {
                            Label("Generate AI hotline voice", systemImage: "waveform")
                            Spacer()
                            if model.isBusy && model.busyLabel.localizedCaseInsensitiveContains("ElevenLabs") {
                                ProgressView()
                            }
                        }
                    }
                    .disabled(model.isBusy)
                    Text("Live ElevenLabs TTS: the voice an AI agent would use to escalate a freeze to a fraud hotline.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Last result") {
                    Text(model.statusMessage)
                        .font(.body.weight(.medium))
                    if let err = model.lastError {
                        Text(err).foregroundStyle(.orange)
                    }
                    if model.bank?.restricted == true {
                        Text("Account is frozen — transfers should be blocked.")
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Demo Lab")
            .overlay {
                if model.isBusy {
                    Color.black.opacity(0.12).ignoresSafeArea().allowsHitTesting(false)
                }
            }
        }
    }

    private func scenarioButton(_ title: String, _ name: String) -> some View {
        Button {
            Task { await model.runScenario(name) }
        } label: {
            HStack {
                Text(title)
                Spacer()
                if model.isBusy && model.busyLabel.contains("scenario") {
                    ProgressView()
                }
            }
        }
        .disabled(model.isBusy)
    }
}
