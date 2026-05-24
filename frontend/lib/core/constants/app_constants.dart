class AppConstants {
  static const String appName = 'Scancourse';
  static const String tagline = 'Scan your results. Plan your future.';

  // API
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://scancourse-sf8zg.ondigitalocean.app/api/v1',
  );

  // Local storage keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userKey = 'user_data';
  static const String onboardingDoneKey = 'onboarding_done';

  // APS rating thresholds
  static const int apsExcellent = 35;
  static const int apsGood = 28;
  static const int apsFair = 20;

  // Provinces
  static const Map<String, String> provinces = {
    'GP': 'Gauteng',
    'WC': 'Western Cape',
    'KZN': 'KwaZulu-Natal',
    'EC': 'Eastern Cape',
    'MP': 'Mpumalanga',
    'LP': 'Limpopo',
    'NW': 'North West',
    'NC': 'Northern Cape',
    'FS': 'Free State',
  };

  // Study fields
  static const Map<String, String> studyFields = {
    'engineering': 'Engineering & Technology',
    'health': 'Health Sciences',
    'business': 'Business & Commerce',
    'law': 'Law',
    'humanities': 'Humanities & Social Sciences',
    'science': 'Natural Sciences',
    'education': 'Education',
    'arts': 'Arts & Design',
    'agriculture': 'Agriculture',
    'ict': 'ICT',
    'built_environment': 'Built Environment',
    'other': 'Other',
  };

  // Grade options
  static const Map<String, String> grades = {
    'grade_10': 'Grade 10',
    'grade_11': 'Grade 11',
    'grade_12': 'Grade 12',
    'gap_year': 'Gap Year',
    'other': 'Other',
  };
}
