"""
Grades all sections matching the format 'type' with an equal weight.
"""
import logging
import random
from xmodule.graders import CourseGrader
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger("edx.graders")


class AssignmentFormatGrader(CourseGrader):
    """
    Grades all sections matching the format 'type' with an equal weight. A specified
    number of lowest scores can be dropped from the calculation. The minimum number of
    sections in this format must be specified (even if those sections haven't been
    written yet).

    min_count defines how many assignments are expected throughout the course. Placeholder
    scores (of 0) will be inserted if the number of matching sections in the course is < min_count.
    If there number of matching sections in the course is > min_count, min_count will be ignored.

    show_only_average is to suppress the display of each assignment in this grader and instead
    only show the total score of this grader in the breakdown.

    hide_average is to suppress the display of the total score in this grader and instead
    only show each assignment in this grader in the breakdown.

    If there is only a single assignment in this grader, then it returns only one entry for the
    grader.  Since the assignment and the total are the same, the total is returned but is not
    labeled as an average.

    category should be presentable to the user, but may not appear. When the grade breakdown is
    displayed, scores from the same category will be similar (for example, by color).

    section_type is a string that is the type of a singular section. For example, for Labs it
    would be "Lab". This defaults to be the same as category.

    short_label is similar to section_type, but shorter. For example, for Homework it would be
    "HW".

    starting_index is the first number that will appear. For example, starting_index=3 and
    min_count = 2 would produce the labels "Assignment 3", "Assignment 4"

    """
    def __init__(
            self,
            type,  # pylint: disable=redefined-builtin
            min_count,
            drop_count,
            category=None,
            section_type=None,
            short_label=None,
            show_only_average=False,
            hide_average=False,
            starting_index=1
    ):
        self.type = type
        self.min_count = min_count
        self.drop_count = drop_count
        self.category = category or self.type
        self.section_type = section_type or self.type
        self.short_label = short_label or self.type
        self.show_only_average = show_only_average
        self.starting_index = starting_index
        self.hide_average = hide_average

    def total_with_drops(self, breakdown):
        """
        Calculates total score for a section while dropping lowest scores
        """
        # Create an array of tuples with (index, mark), sorted by mark['percent'] descending
        sorted_breakdown = sorted(enumerate(breakdown), key=lambda x: -x[1]['percent'])

        # A list of the indices of the dropped scores
        dropped_indices = []
        if self.drop_count > 0:
            dropped_indices = [x[0] for x in sorted_breakdown[-self.drop_count:]]
        aggregate_score = 0
        for index, mark in enumerate(breakdown):
            if index not in dropped_indices:
                aggregate_score += mark['percent']

        if len(breakdown) - self.drop_count > 0:
            aggregate_score /= len(breakdown) - self.drop_count

        return aggregate_score, dropped_indices

    def grade(self, grade_sheet, generate_random_scores=False, unpublished_graded_verticals=None):
        scores = grade_sheet.get(self.type, {}).values()
        breakdown = []
        for i in range(max(self.min_count, len(scores))):
            if i < len(scores) or generate_random_scores:
                if generate_random_scores:  	# for debugging!
                    earned = random.randint(2, 15)
                    possible = random.randint(earned, 15)
                    section_name = _("Generated")

                else:
                    earned = scores[i].graded_total.earned
                    possible = scores[i].graded_total.possible
                    section_name = scores[i].display_name

                percentage = scores[i].percent_graded
                summary_format = u"{section_type} {index} - {name} - {percent:.0%} ({earned:.3n}/{possible:.3n})"
                summary = summary_format.format(
                    index=i + self.starting_index,
                    section_type=self.section_type,
                    name=section_name,
                    percent=percentage,
                    earned=float(earned),
                    possible=float(possible)
                )
            else:
                percentage = 0.0
                # Translators: "Homework 1 - Unreleased - 0% (?/?)" The section has not been released for viewing.
                summary = _(u"{section_type} {index} Unreleased - 0% (?/?)").format(
                    index=i + self.starting_index,
                    section_type=self.section_type
                )
            short_label = u"{short_label} {index:02d}".format(
                index=i + self.starting_index,
                short_label=self.short_label
            )

            breakdown.append({'percent': percentage, 'label': short_label,
                              'detail': summary, 'category': self.category})

        total_percent, dropped_indices = self.total_with_drops(breakdown)

        for dropped_index in dropped_indices:
            breakdown[dropped_index]['mark'] = {
                'detail': _(u"The lowest {drop_count} {section_type} scores are dropped.").format(
                    drop_count=self.drop_count,
                    section_type=self.section_type
                )
            }

        if len(breakdown) == 1:
            # if there is only one entry in a section, suppress the existing individual entry and the average,
            # and just display a single entry for the section.
            total_detail = u"{section_type} = {percent:.0%}".format(
                percent=total_percent,
                section_type=self.section_type,
            )
            total_label = u"{short_label}".format(short_label=self.short_label)
            breakdown = [{'percent': total_percent, 'label': total_label,
                          'detail': total_detail, 'category': self.category, 'prominent': True}, ]
        else:
            # Translators: "Homework Average = 0%"
            total_detail = _(u"{section_type} Average = {percent:.0%}").format(
                percent=total_percent,
                section_type=self.section_type
            )
            # Translators: Avg is short for Average
            total_label = _(u"{short_label} Avg").format(short_label=self.short_label)

            if self.show_only_average:
                breakdown = []

            if not self.hide_average:
                breakdown.append({'percent': total_percent, 'label': total_label,
                                  'detail': total_detail, 'category': self.category, 'prominent': True})

        return {
            'percent': total_percent,
            'section_breakdown': breakdown,
            # No grade_breakdown here
        }
