from django.db import models
from apps.courses.models import Course
from apps.institutions.models import Institution


class DataSource(models.Model):
    """
    Provenance for every data point — critical for trust.
    Examples: StatsSA QLFS Q3 2024, CHE VitalStats, university tracer studies, PayScale.
    """
    name = models.CharField(max_length=300)
    publisher = models.CharField(max_length=200, help_text='e.g. Stats SA, CHE, PayScale')
    url = models.URLField(blank=True)
    publication_date = models.DateField(null=True, blank=True)
    methodology_note = models.TextField(blank=True)
    sample_size = models.PositiveIntegerField(null=True, blank=True)
    is_primary = models.BooleanField(default=False, help_text='Primary research vs. aggregator')

    class Meta:
        db_table = 'outcome_data_sources'
        ordering = ['-publication_date']

    def __str__(self):
        return f'{self.name} ({self.publisher})'


class EmploymentSector(models.Model):
    """Reference table: industries graduates go into."""
    name = models.CharField(max_length=150, unique=True)
    sasic_code = models.CharField(max_length=10, blank=True, help_text='SA Standard Industrial Classification')
    icon_emoji = models.CharField(max_length=4, blank=True)

    class Meta:
        db_table = 'employment_sectors'
        ordering = ['name']

    def __str__(self):
        return self.name


class Employer(models.Model):
    """Companies known to hire graduates from a given course."""
    name = models.CharField(max_length=200, unique=True)
    sector = models.ForeignKey(EmploymentSector, on_delete=models.SET_NULL, null=True, blank=True)
    is_jse_listed = models.BooleanField(default=False)
    headquarters_city = models.CharField(max_length=100, blank=True)
    employee_count_range = models.CharField(max_length=50, blank=True, help_text='e.g. "10000+", "1000-5000"')
    logo = models.ImageField(upload_to='employers/logos/', null=True, blank=True)
    website = models.URLField(blank=True)

    class Meta:
        db_table = 'employers'
        ordering = ['name']

    def __str__(self):
        return self.name


class CourseOutcome(models.Model):
    """
    Aggregate outcome stats for a course (optionally tied to an institution).
    If institution is null, this is the national/sector aggregate for the course.
    """

    EMPLOYMENT_LEVEL = [
        ('low', 'Below 50% employed'),
        ('medium', '50-75% employed'),
        ('high', '75-90% employed'),
        ('excellent', '>90% employed'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='outcomes')
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, null=True, blank=True, related_name='course_outcomes',
    )
    data_year = models.PositiveSmallIntegerField(help_text='Year of the underlying study')
    cohort_size = models.PositiveIntegerField(null=True, blank=True, help_text='Number of graduates surveyed')

    # Employment metrics
    employment_rate_6m = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='% employed within 6 months of graduating',
    )
    employment_rate_12m = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='% employed within 12 months',
    )
    further_study_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='% who pursued postgraduate or professional studies',
    )
    self_employed_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )
    unemployment_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )

    # Salary in ZAR (monthly)
    salary_entry_p25 = models.PositiveIntegerField(null=True, blank=True, help_text='Entry salary 25th percentile')
    salary_entry_median = models.PositiveIntegerField(null=True, blank=True)
    salary_entry_p75 = models.PositiveIntegerField(null=True, blank=True)

    salary_5yr_p25 = models.PositiveIntegerField(null=True, blank=True, help_text='5-years experience 25th percentile')
    salary_5yr_median = models.PositiveIntegerField(null=True, blank=True)
    salary_5yr_p75 = models.PositiveIntegerField(null=True, blank=True)

    salary_10yr_median = models.PositiveIntegerField(null=True, blank=True, help_text='10-year median salary')

    # Other indicators
    avg_time_to_first_job_months = models.PositiveSmallIntegerField(null=True, blank=True)
    job_satisfaction_score = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        help_text='1-10 from graduate surveys',
    )
    field_match_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='% working in their field of study',
    )

    sources = models.ManyToManyField(DataSource, blank=True, related_name='outcomes')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_outcomes'
        unique_together = ('course', 'institution', 'data_year')
        ordering = ['-data_year', 'course']

    def __str__(self):
        target = self.institution.name if self.institution else 'National'
        return f'{self.course.name} ({target}, {self.data_year})'

    @property
    def employment_level(self) -> str:
        rate = self.employment_rate_12m
        if rate is None:
            return 'unknown'
        rate = float(rate)
        if rate >= 90:
            return 'excellent'
        if rate >= 75:
            return 'high'
        if rate >= 50:
            return 'medium'
        return 'low'


class CourseSectorBreakdown(models.Model):
    """Where do graduates of a course actually work? Top sectors with % share."""
    outcome = models.ForeignKey(CourseOutcome, on_delete=models.CASCADE, related_name='sector_breakdown')
    sector = models.ForeignKey(EmploymentSector, on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    rank = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = 'course_sector_breakdowns'
        ordering = ['rank']
        unique_together = ('outcome', 'sector')


class CourseTopEmployer(models.Model):
    """Top hiring employers for graduates of this course."""
    outcome = models.ForeignKey(CourseOutcome, on_delete=models.CASCADE, related_name='top_employers')
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField(default=1)
    grad_count_estimate = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'course_top_employers'
        ordering = ['rank']
        unique_together = ('outcome', 'employer')


class JobRole(models.Model):
    """Common job titles for graduates of this course."""
    outcome = models.ForeignKey(CourseOutcome, on_delete=models.CASCADE, related_name='job_roles')
    title = models.CharField(max_length=200)
    rank = models.PositiveSmallIntegerField(default=1)
    median_monthly_salary_zar = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'course_job_roles'
        ordering = ['rank']
