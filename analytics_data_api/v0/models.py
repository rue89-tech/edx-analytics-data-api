from django.db import models

from analytics_data_api.constants import country, genders, educ_level


class CourseActivityWeekly(models.Model):
    """A count of unique users who performed a particular action during a week."""

    class Meta(object):
        db_table = 'course_activity'
        index_together = [['course_id', 'activity_type']]
        ordering = ('interval_end', 'interval_start', 'course_id')
        get_latest_by = 'interval_end'

    course_id = models.CharField(db_index=True, max_length=255)
    interval_start = models.DateTimeField()
    interval_end = models.DateTimeField(db_index=True)
    activity_type = models.CharField(db_index=True, max_length=255, db_column='label')
    count = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_most_recent(cls, course_id, activity_type):
        """Activity for the week that was mostly recently computed."""
        return cls.objects.filter(course_id=course_id, activity_type=activity_type).latest('interval_end')


class BaseCourseEnrollment(models.Model):
    course_id = models.CharField(max_length=255)
    date = models.DateField(null=False, db_index=True)
    count = models.IntegerField(null=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        abstract = True
        get_latest_by = 'date'
        index_together = [('course_id', 'date',)]


class CourseEnrollmentDaily(BaseCourseEnrollment):
    class Meta(BaseCourseEnrollment.Meta):
        db_table = 'course_enrollment_daily'
        ordering = ('date', 'course_id')
        unique_together = [('course_id', 'date',)]


class CourseEnrollmentModeDaily(BaseCourseEnrollment):
    mode = models.CharField(max_length=255)
    cumulative_count = models.IntegerField(null=False)

    class Meta(BaseCourseEnrollment.Meta):
        db_table = 'course_enrollment_mode_daily'
        ordering = ('date', 'course_id', 'mode')
        unique_together = [('course_id', 'date', 'mode')]


class CourseEnrollmentByBirthYear(BaseCourseEnrollment):
    birth_year = models.IntegerField(null=False)

    class Meta(BaseCourseEnrollment.Meta):
        db_table = 'course_enrollment_birth_year_daily'
        ordering = ('date', 'course_id', 'birth_year')
        unique_together = [('course_id', 'date', 'birth_year')]


class CourseEnrollmentByEducation(BaseCourseEnrollment):
    education_level = models.CharField(max_length=255, null=True)

    class Meta(BaseCourseEnrollment.Meta):
        db_table = 'course_enrollment_education_level_daily'
        ordering = ('date', 'course_id', 'education_level')
        unique_together = [('course_id', 'date', 'education_level')]


class CourseEnrollmentByGender(BaseCourseEnrollment):
    gender = models.CharField(max_length=255, null=True, db_column='gender')

    @property
    def cleaned_gender(self):
        """
        Returns the gender with full names and 'unknown' replacing null/None.
        """
        return genders.CLEANED_GENDERS.get(self.gender, genders.UNKNOWN)

    class Meta(BaseCourseEnrollment.Meta):
        db_table = 'course_enrollment_gender_daily'
        ordering = ('date', 'course_id', 'gender')
        unique_together = [('course_id', 'date', 'gender')]


class CourseEnrollmentSnapshot(models.Model):
    """ The most up-to-date enrollment information """
    course_id = models.CharField(max_length=255, null=False)
    user = models.ForeignKey('UserProfile', related_name='courses', null=False, db_column='user_id')
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        db_table = 'course_enrollment_snapshot'
        unique_together = [('course_id', 'user',)]


class BaseProblemResponseAnswerDistribution(models.Model):
    """ Base model for the answer_distribution table. """

    class Meta(object):
        db_table = 'answer_distribution'
        abstract = True

    course_id = models.CharField(db_index=True, max_length=255)
    module_id = models.CharField(db_index=True, max_length=255)
    part_id = models.CharField(db_index=True, max_length=255)
    correct = models.NullBooleanField()
    value_id = models.CharField(db_index=True, max_length=255, null=True)
    answer_value = models.TextField(null=True, db_column='answer_value_text')
    variant = models.IntegerField(null=True)
    problem_display_name = models.TextField(null=True)
    question_text = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)


class ProblemResponseAnswerDistribution(BaseProblemResponseAnswerDistribution):
    """ Original model for the count of a particular answer to a response to a problem in a course. """

    class Meta(BaseProblemResponseAnswerDistribution.Meta):
        managed = False

    count = models.IntegerField()


class ProblemFirstLastResponseAnswerDistribution(BaseProblemResponseAnswerDistribution):
    """ Updated model for answer_distribution table with counts of first and last attempts at problems. """

    class Meta(BaseProblemResponseAnswerDistribution.Meta):
        verbose_name = 'first_last_answer_distribution'

    first_response_count = models.IntegerField()
    last_response_count = models.IntegerField()


class CourseEnrollmentByCountry(BaseCourseEnrollment):
    country_code = models.CharField(max_length=255, null=False, db_column='country_code')

    @property
    def country(self):
        """
        Returns a Country object representing the country in this model's country_code.
        """
        return country.get_country(self.country_code)

    class Meta(BaseCourseEnrollment.Meta):
        db_table = 'course_enrollment_location_current'
        ordering = ('date', 'course_id', 'country_code')
        unique_together = [('course_id', 'date', 'country_code')]


class GradeDistribution(models.Model):
    """ Each row stores the count of a particular grade on a module for a given course. """

    class Meta(object):
        db_table = 'grade_distribution'

    module_id = models.CharField(db_index=True, max_length=255)
    course_id = models.CharField(db_index=True, max_length=255)
    grade = models.IntegerField()
    max_grade = models.IntegerField()
    count = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)


class SequentialOpenDistribution(models.Model):
    """ Each row stores the count of views a particular module has had in a given course. """

    class Meta(object):
        db_table = 'sequential_open_distribution'

    module_id = models.CharField(db_index=True, max_length=255)
    course_id = models.CharField(db_index=True, max_length=255)
    count = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)


class TypologyEntry(models.Model):
    """ Categorization of students into 'types' per course section """
    course_id = models.CharField(db_index=True, max_length=255)
    chapter_id = models.CharField(max_length=255)
    video_type = models.IntegerField(null=False)
    problem_type = models.IntegerField(null=False)
    num_users = models.IntegerField(null=False)  # The number of users who match video_type and problem_type
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        db_table = 'trajectory'


class UserProfile(models.Model):
    """ User Account and Profile information """
    username = models.CharField(max_length=30, unique=True, db_index=True)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    is_staff = models.BooleanField(default=False, null=False)
    email = models.EmailField(blank=True, max_length=75)
    name = models.CharField(max_length=255)
    gender_raw = models.CharField(max_length=6, null=True, db_column='gender')
    year_of_birth = models.IntegerField(null=True)
    level_of_education_raw = models.CharField(max_length=6, null=True, db_column='level_of_education')

    @property
    def gender(self):
        """
        Returns the gender with full names and 'unknown' replacing null/None.
        """
        return genders.CLEANED_GENDERS.get(self.gender_raw, genders.UNKNOWN)

    @property
    def level_of_education(self):
        """
        Returns the user's level of education with 'unknown' replacing null/None.
        """
        return educ_level.EDUCATION_LEVELS.get(self.level_of_education_raw, educ_level.UNKNOWN)

    class Meta(object):
        db_table = 'user_profile'


class UserProblemWeeklyData(models.Model):
    """ User problem history per week """
    week_ending = models.DateField()
    course_id = models.CharField(max_length=255)
    user_id = models.IntegerField()
    problem_id = models.CharField(max_length=255)
    num_attempts = models.IntegerField()
    most_recent_score = models.IntegerField()
    max_score = models.IntegerField()

    class Meta(object):
        db_table = 'user_problem_weekly_data'
        ordering = ('week_ending',)


class BaseVideo(models.Model):
    """ Base video model. """
    pipeline_video_id = models.CharField(db_index=True, max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        abstract = True


class VideoTimeline(BaseVideo):
    """ Timeline of video segments. """

    segment = models.IntegerField()
    num_users = models.IntegerField()
    num_views = models.IntegerField()

    class Meta(BaseVideo.Meta):
        db_table = 'video_timeline'


class Video(BaseVideo):
    """ Videos associated with a particular course. """

    course_id = models.CharField(db_index=True, max_length=255)
    encoded_module_id = models.CharField(db_index=True, max_length=255)
    duration = models.IntegerField()
    segment_length = models.IntegerField()
    users_at_start = models.IntegerField()
    users_at_end = models.IntegerField()

    class Meta(BaseVideo.Meta):
        db_table = 'video'
