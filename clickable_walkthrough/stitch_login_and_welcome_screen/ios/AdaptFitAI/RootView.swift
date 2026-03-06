import SwiftUI

struct RootView: View {
  var body: some View {
    NavigationStack {
      List {
        Section("Demo flow") {
          NavigationLink("Run demo flow", destination: FlowView())
        }

        Section("All screens") {
          ForEach(Screen.allCases) { screen in
            NavigationLink(screen.title) {
              ScreenDetailView(screen: screen)
            }
          }
        }
      }
      .navigationTitle("AdaptFit AI")
    }
  }
}

struct ScreenDetailView: View {
  let screen: Screen

  var body: some View {
    ScreenWebView(screen: screen)
      .navigationTitle(screen.title)
      .navigationBarTitleDisplayMode(.inline)
  }
}

#Preview {
  RootView()
}

