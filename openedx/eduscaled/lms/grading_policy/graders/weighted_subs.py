"""
This grader takes a list of tuples containing (grader, category_name, weight) and computes
a final grade by totalling the contribution of each sub grader and multiplying it by the
given weight.
"""
import logging
from collections import OrderedDict
from django.utils.translation import ugettext as _
from xmodule.graders import CourseGrader

log = logging.getLogger("edx.graders")


class WeightedSubsectionsGrader(CourseGrader):
    """
    This grader takes a list of tuples containing (grader, category_name, weight) and computes
    a final grade by totalling the contribution of each sub grader and multiplying it by the
    given weight. For example, the sections may be

    [ (homeworkGrader, "Homework", 0.15), (labGrader, "Labs", 0.15), (midtermGrader, "Midterm", 0.30),
      (finalGrader, "Final", 0.40) ]

    All items in section_breakdown for each subgrader will be combined. A grade_breakdown will be
    composed using the score from each grader.

    Note that the sum of the weights is not taken into consideration. If the weights add up to
    a value > 1, the student may end up with a percent > 100%. This allows for sections that
    are extra credit.
    """
    def __init__(self, subgraders):
        self.subgraders = subgraders

    @property
    def sum_of_weights(self):
        sum = 0
        for _, _, weight, _ in self.subgraders:
            sum += weight
        return sum

    def grade(self, grade_sheet, generate_random_scores=False, unpublished_graded_verticals=None):
        if unpublished_graded_verticals is None:
            unpublished_graded_verticals = {}
        total_percent = 0.0
        section_breakdown = []
        grade_breakdown = OrderedDict()

        for subgrader, assignment_type, weight, passing_grade in self.subgraders:
            subgrade_result = subgrader.grade(grade_sheet, generate_random_scores, unpublished_graded_verticals)

            weighted_percent = subgrade_result['percent'] * weight
            section_detail = _(u"{assignment_type} = {weighted_percent:.2%} of a possible {weight:.2%}").format(
                assignment_type=assignment_type,
                weighted_percent=weighted_percent,
                weight=weight)

            total_percent += weighted_percent
            section_breakdown += subgrade_result['section_breakdown']
            grade_breakdown[assignment_type] = {
                'percent': weighted_percent,
                'detail': section_detail,
                'category': assignment_type,
                'is_passed': subgrade_result['percent'] >= passing_grade,
            }

        return {
            'percent': total_percent,
            'section_breakdown': section_breakdown,
            'sections_passed': all(section['is_passed'] for section in grade_breakdown.values()),
            'grade_breakdown': grade_breakdown
        }
