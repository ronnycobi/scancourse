class OutcomeData {
  final int id;
  final String courseName;
  final String? institutionName;
  final int dataYear;
  final int? cohortSize;

  final double? employmentRate6m;
  final double? employmentRate12m;
  final double? furtherStudyRate;
  final double? selfEmployedRate;
  final double? unemploymentRate;
  final String employmentLevel;

  final int? salaryEntryP25;
  final int? salaryEntryMedian;
  final int? salaryEntryP75;
  final int? salary5yrP25;
  final int? salary5yrMedian;
  final int? salary5yrP75;
  final int? salary10yrMedian;

  final int? avgTimeToFirstJobMonths;
  final double? jobSatisfactionScore;
  final double? fieldMatchRate;

  final List<SectorBreakdown> sectorBreakdown;
  final List<TopEmployer> topEmployers;
  final List<JobRole> jobRoles;
  final List<DataSource> sources;

  OutcomeData({
    required this.id,
    required this.courseName,
    this.institutionName,
    required this.dataYear,
    this.cohortSize,
    this.employmentRate6m,
    this.employmentRate12m,
    this.furtherStudyRate,
    this.selfEmployedRate,
    this.unemploymentRate,
    required this.employmentLevel,
    this.salaryEntryP25,
    this.salaryEntryMedian,
    this.salaryEntryP75,
    this.salary5yrP25,
    this.salary5yrMedian,
    this.salary5yrP75,
    this.salary10yrMedian,
    this.avgTimeToFirstJobMonths,
    this.jobSatisfactionScore,
    this.fieldMatchRate,
    required this.sectorBreakdown,
    required this.topEmployers,
    required this.jobRoles,
    required this.sources,
  });

  factory OutcomeData.fromJson(Map<String, dynamic> j) {
    double? toD(v) => v == null ? null : double.tryParse(v.toString());
    return OutcomeData(
      id: j['id'],
      courseName: j['course_name'] ?? '',
      institutionName: j['institution_name'],
      dataYear: j['data_year'],
      cohortSize: j['cohort_size'],
      employmentRate6m: toD(j['employment_rate_6m']),
      employmentRate12m: toD(j['employment_rate_12m']),
      furtherStudyRate: toD(j['further_study_rate']),
      selfEmployedRate: toD(j['self_employed_rate']),
      unemploymentRate: toD(j['unemployment_rate']),
      employmentLevel: j['employment_level'] ?? 'unknown',
      salaryEntryP25: j['salary_entry_p25'],
      salaryEntryMedian: j['salary_entry_median'],
      salaryEntryP75: j['salary_entry_p75'],
      salary5yrP25: j['salary_5yr_p25'],
      salary5yrMedian: j['salary_5yr_median'],
      salary5yrP75: j['salary_5yr_p75'],
      salary10yrMedian: j['salary_10yr_median'],
      avgTimeToFirstJobMonths: j['avg_time_to_first_job_months'],
      jobSatisfactionScore: toD(j['job_satisfaction_score']),
      fieldMatchRate: toD(j['field_match_rate']),
      sectorBreakdown: ((j['sector_breakdown'] ?? []) as List)
          .map((s) => SectorBreakdown.fromJson(Map<String, dynamic>.from(s))).toList(),
      topEmployers: ((j['top_employers'] ?? []) as List)
          .map((e) => TopEmployer.fromJson(Map<String, dynamic>.from(e))).toList(),
      jobRoles: ((j['job_roles'] ?? []) as List)
          .map((r) => JobRole.fromJson(Map<String, dynamic>.from(r))).toList(),
      sources: ((j['sources'] ?? []) as List)
          .map((s) => DataSource.fromJson(Map<String, dynamic>.from(s))).toList(),
    );
  }
}

class SectorBreakdown {
  final String sectorName;
  final String sectorEmoji;
  final double percentage;
  final int rank;

  SectorBreakdown({required this.sectorName, required this.sectorEmoji, required this.percentage, required this.rank});

  factory SectorBreakdown.fromJson(Map<String, dynamic> j) => SectorBreakdown(
    sectorName: j['sector_name'] ?? '',
    sectorEmoji: j['sector_emoji'] ?? '🏢',
    percentage: double.tryParse((j['percentage'] ?? 0).toString()) ?? 0,
    rank: j['rank'] ?? 0,
  );
}

class TopEmployer {
  final int? employerId;
  final String name;
  final String? sectorName;
  final bool isJseListed;
  final String? logo;
  final int rank;

  TopEmployer({this.employerId, required this.name, this.sectorName, required this.isJseListed, this.logo, required this.rank});

  factory TopEmployer.fromJson(Map<String, dynamic> j) {
    final emp = j['employer'] as Map<String, dynamic>? ?? {};
    return TopEmployer(
      employerId: emp['id'],
      name: emp['name'] ?? '',
      sectorName: emp['sector_name'],
      isJseListed: emp['is_jse_listed'] ?? false,
      logo: emp['logo'],
      rank: j['rank'] ?? 0,
    );
  }
}

class JobRole {
  final String title;
  final int rank;
  final int? medianMonthlySalaryZar;
  final String description;

  JobRole({required this.title, required this.rank, this.medianMonthlySalaryZar, required this.description});

  factory JobRole.fromJson(Map<String, dynamic> j) => JobRole(
    title: j['title'] ?? '',
    rank: j['rank'] ?? 0,
    medianMonthlySalaryZar: j['median_monthly_salary_zar'],
    description: j['description'] ?? '',
  );
}

class DataSource {
  final String name;
  final String publisher;
  final String? url;
  final String? publicationDate;

  DataSource({required this.name, required this.publisher, this.url, this.publicationDate});

  factory DataSource.fromJson(Map<String, dynamic> j) => DataSource(
    name: j['name'] ?? '',
    publisher: j['publisher'] ?? '',
    url: j['url'],
    publicationDate: j['publication_date'],
  );
}
