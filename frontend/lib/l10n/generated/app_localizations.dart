import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_af.dart';
import 'app_localizations_en.dart';
import 'app_localizations_st.dart';
import 'app_localizations_xh.dart';
import 'app_localizations_zu.dart';

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates = <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('af'),
    Locale('en'),
    Locale('st'),
    Locale('xh'),
    Locale('zu')
  ];

  /// No description provided for @appName.
  ///
  /// In en, this message translates to:
  /// **'Scancourse'**
  String get appName;

  /// No description provided for @tagline.
  ///
  /// In en, this message translates to:
  /// **'Scan your results. Plan your future.'**
  String get tagline;

  /// No description provided for @welcomeBack.
  ///
  /// In en, this message translates to:
  /// **'Welcome back!'**
  String get welcomeBack;

  /// No description provided for @signInPrompt.
  ///
  /// In en, this message translates to:
  /// **'Sign in to plan your future'**
  String get signInPrompt;

  /// No description provided for @emailAddress.
  ///
  /// In en, this message translates to:
  /// **'Email address'**
  String get emailAddress;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @signIn.
  ///
  /// In en, this message translates to:
  /// **'Sign In'**
  String get signIn;

  /// No description provided for @signUp.
  ///
  /// In en, this message translates to:
  /// **'Sign up'**
  String get signUp;

  /// No description provided for @forgotPassword.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get forgotPassword;

  /// No description provided for @noAccount.
  ///
  /// In en, this message translates to:
  /// **'Don\'t have an account?'**
  String get noAccount;

  /// No description provided for @createAccount.
  ///
  /// In en, this message translates to:
  /// **'Create Account'**
  String get createAccount;

  /// No description provided for @continueWithGoogle.
  ///
  /// In en, this message translates to:
  /// **'Continue with Google'**
  String get continueWithGoogle;

  /// No description provided for @whatGrade.
  ///
  /// In en, this message translates to:
  /// **'What grade are you in?'**
  String get whatGrade;

  /// No description provided for @whichProvince.
  ///
  /// In en, this message translates to:
  /// **'Which province are you in?'**
  String get whichProvince;

  /// No description provided for @whichField.
  ///
  /// In en, this message translates to:
  /// **'What field interests you?'**
  String get whichField;

  /// No description provided for @studyWhere.
  ///
  /// In en, this message translates to:
  /// **'Where do you want to study?'**
  String get studyWhere;

  /// No description provided for @dreamCareer.
  ///
  /// In en, this message translates to:
  /// **'What\'s your dream career?'**
  String get dreamCareer;

  /// No description provided for @continueLabel.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get continueLabel;

  /// No description provided for @skip.
  ///
  /// In en, this message translates to:
  /// **'Skip'**
  String get skip;

  /// No description provided for @getStarted.
  ///
  /// In en, this message translates to:
  /// **'Get Started'**
  String get getStarted;

  /// No description provided for @calculateAps.
  ///
  /// In en, this message translates to:
  /// **'Calculate your APS'**
  String get calculateAps;

  /// No description provided for @uploadReportPrompt.
  ///
  /// In en, this message translates to:
  /// **'Upload your report card to find matching courses'**
  String get uploadReportPrompt;

  /// No description provided for @upload.
  ///
  /// In en, this message translates to:
  /// **'Upload'**
  String get upload;

  /// No description provided for @camera.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get camera;

  /// No description provided for @enterMarks.
  ///
  /// In en, this message translates to:
  /// **'Enter Marks'**
  String get enterMarks;

  /// No description provided for @yourApsScore.
  ///
  /// In en, this message translates to:
  /// **'Your APS Score'**
  String get yourApsScore;

  /// No description provided for @excellent.
  ///
  /// In en, this message translates to:
  /// **'Excellent'**
  String get excellent;

  /// No description provided for @good.
  ///
  /// In en, this message translates to:
  /// **'Good'**
  String get good;

  /// No description provided for @fair.
  ///
  /// In en, this message translates to:
  /// **'Fair'**
  String get fair;

  /// No description provided for @quickActions.
  ///
  /// In en, this message translates to:
  /// **'Quick Actions'**
  String get quickActions;

  /// No description provided for @findCourses.
  ///
  /// In en, this message translates to:
  /// **'Find Courses'**
  String get findCourses;

  /// No description provided for @bursaries.
  ///
  /// In en, this message translates to:
  /// **'Bursaries'**
  String get bursaries;

  /// No description provided for @askAi.
  ///
  /// In en, this message translates to:
  /// **'Ask AI'**
  String get askAi;

  /// No description provided for @universitiesOpen.
  ///
  /// In en, this message translates to:
  /// **'Universities Still Open'**
  String get universitiesOpen;

  /// No description provided for @bursariesClosingSoon.
  ///
  /// In en, this message translates to:
  /// **'Bursaries Closing Soon'**
  String get bursariesClosingSoon;

  /// No description provided for @seeAll.
  ///
  /// In en, this message translates to:
  /// **'See all'**
  String get seeAll;

  /// No description provided for @scanReportCard.
  ///
  /// In en, this message translates to:
  /// **'Scan Report Card'**
  String get scanReportCard;

  /// No description provided for @uploadReportCard.
  ///
  /// In en, this message translates to:
  /// **'Upload your report card'**
  String get uploadReportCard;

  /// No description provided for @takePhoto.
  ///
  /// In en, this message translates to:
  /// **'Take a Photo'**
  String get takePhoto;

  /// No description provided for @chooseGallery.
  ///
  /// In en, this message translates to:
  /// **'Choose from Gallery'**
  String get chooseGallery;

  /// No description provided for @uploadPdf.
  ///
  /// In en, this message translates to:
  /// **'Upload PDF'**
  String get uploadPdf;

  /// No description provided for @enterMarksManually.
  ///
  /// In en, this message translates to:
  /// **'Enter marks manually instead'**
  String get enterMarksManually;

  /// No description provided for @calculateMyAps.
  ///
  /// In en, this message translates to:
  /// **'Calculate My APS'**
  String get calculateMyAps;

  /// No description provided for @processing.
  ///
  /// In en, this message translates to:
  /// **'Processing your report card...'**
  String get processing;

  /// No description provided for @eligible.
  ///
  /// In en, this message translates to:
  /// **'Eligible'**
  String get eligible;

  /// No description provided for @stretch.
  ///
  /// In en, this message translates to:
  /// **'Stretch'**
  String get stretch;

  /// No description provided for @alternatives.
  ///
  /// In en, this message translates to:
  /// **'Alternatives'**
  String get alternatives;

  /// No description provided for @searchCourses.
  ///
  /// In en, this message translates to:
  /// **'Search courses...'**
  String get searchCourses;

  /// No description provided for @aboutCourse.
  ///
  /// In en, this message translates to:
  /// **'About this course'**
  String get aboutCourse;

  /// No description provided for @careerOpportunities.
  ///
  /// In en, this message translates to:
  /// **'Career Opportunities'**
  String get careerOpportunities;

  /// No description provided for @applyNow.
  ///
  /// In en, this message translates to:
  /// **'Apply Now'**
  String get applyNow;

  /// No description provided for @institutionsOffering.
  ///
  /// In en, this message translates to:
  /// **'Institutions Offering This'**
  String get institutionsOffering;

  /// No description provided for @field.
  ///
  /// In en, this message translates to:
  /// **'Field'**
  String get field;

  /// No description provided for @province.
  ///
  /// In en, this message translates to:
  /// **'Province'**
  String get province;

  /// No description provided for @type.
  ///
  /// In en, this message translates to:
  /// **'Type'**
  String get type;

  /// No description provided for @deadline.
  ///
  /// In en, this message translates to:
  /// **'Deadline'**
  String get deadline;

  /// No description provided for @myProfile.
  ///
  /// In en, this message translates to:
  /// **'My Profile'**
  String get myProfile;

  /// No description provided for @signOut.
  ///
  /// In en, this message translates to:
  /// **'Sign Out'**
  String get signOut;

  /// No description provided for @savedItems.
  ///
  /// In en, this message translates to:
  /// **'Saved Items'**
  String get savedItems;

  /// No description provided for @myReports.
  ///
  /// In en, this message translates to:
  /// **'My Reports'**
  String get myReports;

  /// No description provided for @notifications.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get notifications;

  /// No description provided for @settings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @privacy.
  ///
  /// In en, this message translates to:
  /// **'Privacy'**
  String get privacy;

  /// No description provided for @yourStudyGuide.
  ///
  /// In en, this message translates to:
  /// **'Your study guide'**
  String get yourStudyGuide;

  /// No description provided for @askAnything.
  ///
  /// In en, this message translates to:
  /// **'Ask me anything about studying...'**
  String get askAnything;

  /// No description provided for @errorGeneric.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get errorGeneric;

  /// No description provided for @loading.
  ///
  /// In en, this message translates to:
  /// **'Loading...'**
  String get loading;

  /// No description provided for @noResults.
  ///
  /// In en, this message translates to:
  /// **'No results found'**
  String get noResults;

  /// No description provided for @tryAdjusting.
  ///
  /// In en, this message translates to:
  /// **'Try adjusting your filters'**
  String get tryAdjusting;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @submit.
  ///
  /// In en, this message translates to:
  /// **'Submit'**
  String get submit;

  /// No description provided for @yes.
  ///
  /// In en, this message translates to:
  /// **'Yes'**
  String get yes;

  /// No description provided for @no.
  ///
  /// In en, this message translates to:
  /// **'No'**
  String get no;

  /// No description provided for @applicationTracker.
  ///
  /// In en, this message translates to:
  /// **'Applications'**
  String get applicationTracker;

  /// No description provided for @documentVault.
  ///
  /// In en, this message translates to:
  /// **'Documents'**
  String get documentVault;

  /// No description provided for @roommates.
  ///
  /// In en, this message translates to:
  /// **'Roommates'**
  String get roommates;

  /// No description provided for @motivationLetter.
  ///
  /// In en, this message translates to:
  /// **'Motivation Letter'**
  String get motivationLetter;
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>['af', 'en', 'st', 'xh', 'zu'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {


  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'af': return AppLocalizationsAf();
    case 'en': return AppLocalizationsEn();
    case 'st': return AppLocalizationsSt();
    case 'xh': return AppLocalizationsXh();
    case 'zu': return AppLocalizationsZu();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.'
  );
}
