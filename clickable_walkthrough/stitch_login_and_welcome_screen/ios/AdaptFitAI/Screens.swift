import Foundation

enum Screen: String, CaseIterable, Identifiable {
  case loginAndWelcome = "login_and_welcome_screen"
  case userProfileSetup = "user_profile_setup"
  case injuryIdentification = "injury_identification"
  case injuryAssessmentQuestionnaire = "injury_assessment_questionnaire"
  case chooseGenerationPath = "choose_generation_path"
  case importOrPasteWorkout = "import_or_paste_workout"
  case workoutTypeSelection = "workout_type_selection"
  case strengthTrainingSetup = "strength_training_setup"
  case aiGenerationLoadingState = "ai_generation_loading_state"
  case newTailoredWorkoutPlan = "new_tailored_workout_plan"
  case modifiedWorkoutResults = "modified_workout_results"
  case recoveryReadinessResult = "recovery_readiness_result"
  case notClearedEvaluationResult = "not_cleared_evaluation_result"

  var id: String { rawValue }

  var title: String {
    switch self {
    case .loginAndWelcome: "Login & Welcome"
    case .userProfileSetup: "User Profile Setup"
    case .injuryIdentification: "Injury Identification"
    case .injuryAssessmentQuestionnaire: "Injury Assessment"
    case .chooseGenerationPath: "Choose Generation Path"
    case .importOrPasteWorkout: "Import or Paste Workout"
    case .workoutTypeSelection: "Workout Type Selection"
    case .strengthTrainingSetup: "Strength Training Setup"
    case .aiGenerationLoadingState: "AI Generation Loading"
    case .newTailoredWorkoutPlan: "New Tailored Workout Plan"
    case .modifiedWorkoutResults: "Modified Workout Results"
    case .recoveryReadinessResult: "Recovery Readiness Result"
    case .notClearedEvaluationResult: "Not Cleared Evaluation Result"
    }
  }

  var resourceName: String { rawValue }
}

extension Screen {
  static let demoFlow: [Screen] = [
    .loginAndWelcome,
    .userProfileSetup,
    .injuryIdentification,
    .injuryAssessmentQuestionnaire,
    .chooseGenerationPath,
    .importOrPasteWorkout,
    .workoutTypeSelection,
    .strengthTrainingSetup,
    .aiGenerationLoadingState,
    .newTailoredWorkoutPlan,
    .modifiedWorkoutResults,
    .recoveryReadinessResult,
    .notClearedEvaluationResult,
  ]
}

