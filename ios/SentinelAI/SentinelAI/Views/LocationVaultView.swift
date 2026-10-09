import MapKit
import SwiftUI

struct LocationVaultView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        NavigationStack {
            List {
                Section("Controls") {
                    Button("Request Location Permission") {
                        model.location.requestPermission()
                    }
                    Button("Update my location") {
                        Task {
                            await model.location.captureAndUpload()
                            await model.refreshAll()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    Text("Sentinel uses this privately to verify purchases. Coordinates stay in your protected vault.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Toggle("Pause tracking", isOn: Binding(
                        get: { model.location.isPaused },
                        set: { paused in
                            if paused { model.location.pause() } else { model.location.start() }
                        }
                    ))
                    Text(model.location.lastUploadMessage)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let err = model.location.lastError {
                        Text(err).font(.caption).foregroundStyle(.orange)
                    }
                }

                Section("Live fix") {
                    if let loc = model.location.lastLocation {
                        Text(String(format: "%.6f, %.6f ±%.0fm", loc.coordinate.latitude, loc.coordinate.longitude, loc.horizontalAccuracy))
                            .font(.system(.body, design: .monospaced))
                        Map(initialPosition: .region(MKCoordinateRegion(
                            center: loc.coordinate,
                            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
                        ))) {
                            Marker("You", coordinate: loc.coordinate)
                        }
                        .frame(height: 200)
                        .listRowInsets(EdgeInsets())
                    } else {
                        Text("Waiting for Core Location fix…")
                    }
                }

                Section("History from backend") {
                    ForEach(model.gpsEvents) { event in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(String(format: "%.5f, %.5f", event.lat, event.lon))
                                .font(.system(.body, design: .monospaced))
                            Text("\(event.eventTimestamp) · ±\(Int(event.horizontalAccuracyM))m · \(event.synthetic ? "scenario" : "device")")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Location Vault")
            .task {
                model.location.requestPermission()
                await model.refreshAll()
            }
        }
    }
}
