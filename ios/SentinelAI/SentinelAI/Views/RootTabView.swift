import SwiftUI

struct RootTabView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Home", systemImage: "shield.lefthalf.filled") }
            TransactionsView()
                .tabItem { Label("Activity", systemImage: "creditcard") }
            IncidentsView()
                .tabItem { Label("Alerts", systemImage: "bell") }
            LocationVaultView()
                .tabItem { Label("Location", systemImage: "location.fill") }
            DemoLabView()
                .tabItem { Label("Demo", systemImage: "flask") }
        }
        .tint(Color(red: 0.35, green: 0.85, blue: 0.72))
        .overlay(alignment: .top) {
            if model.isBusy {
                HStack(spacing: 10) {
                    ProgressView()
                        .tint(.white)
                    Text(model.busyLabel.isEmpty ? "Working…" : model.busyLabel)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.white)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color.black.opacity(0.75), in: Capsule())
                .padding(.top, 8)
                .transition(.move(edge: .top).combined(with: .opacity))
                .animation(.easeInOut(duration: 0.2), value: model.isBusy)
            }
        }
        .alert(
            model.feedback?.title ?? "",
            isPresented: Binding(
                get: { model.feedback != nil },
                set: { if !$0 { model.dismissFeedback() } }
            )
        ) {
            Button("OK", role: .cancel) { model.dismissFeedback() }
        } message: {
            Text(model.feedback?.message ?? "")
        }
    }
}
