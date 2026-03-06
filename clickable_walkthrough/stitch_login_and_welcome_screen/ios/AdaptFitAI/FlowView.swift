import SwiftUI

struct FlowView: View {
  @Environment(\.dismiss) private var dismiss
  @State private var index: Int = 0

  private var screens: [Screen] { Screen.demoFlow }
  private var screen: Screen { screens[index] }

  var body: some View {
    ScreenWebView(screen: screen)
      .safeAreaInset(edge: .bottom) {
        VStack(spacing: 0) {
          Divider()

          HStack(spacing: 12) {
            Button {
              if index > 0 { index -= 1 }
            } label: {
              Label("Back", systemImage: "chevron.left")
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .disabled(index == 0)

            Button {
              if index < screens.count - 1 {
                index += 1
              } else {
                dismiss()
              }
            } label: {
              Label(index == screens.count - 1 ? "Done" : "Next", systemImage: "chevron.right")
                .labelStyle(.titleAndIcon)
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
          }
          .padding()
          .background(.thinMaterial)
        }
      }
    .navigationTitle("\(index + 1) / \(screens.count)")
    .navigationBarTitleDisplayMode(.inline)
  }
}

#Preview {
  NavigationStack {
    FlowView()
  }
}

