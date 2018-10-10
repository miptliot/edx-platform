""""
Grades all sections matching the format 'type' taking into account a weight.
"""
import logging
import random
from django.utils.translation import ugettext as _
from xmodule.graders import CourseGrader

log = logging.getLogger("edx.graders")


class WeightedAssignmentFormatGrader(CourseGrader):
    """
    Grades all sections matching the format 'type' taking into account a weight. A specified
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

    If there is only a single assignment in this grader, then it acts like a SingleSectionGrader
    and returns only one entry for the grader.  Since the assignment and the total are the same,
    the total is returned but is not labeled as an average.

    category should be presentable to the user, but may not appear. When the grade breakdown is
    displayed, scores from the same category will be similar (for example, by color).

    section_type is a string that is the type of a singular section. For example, for Labs it
    would be "Lab". This defaults to be the same as category.

    short_label is similar to section_type, but shorter. For example, for Homework it would be
    "HW".

    starting_index is the first number that will appear. For example, starting_index=3 and
    min_count = 2 would produce the labels "Assignment 3", "Assignment 4"
    """
    # pylint: disable=redefined-builtin
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

    def grade(self, grade_sheet, generate_random_scores=False, unpublished_graded_verticals=dict()):
        def total_with_drops(breakdown, drop_count):
            """
            Calculates total score for a section while dropping lowest scores
            """
            # Create an array of tuples with (index, mark), sorted by mark['percent'] descending
            sorted_breakdown = sorted(enumerate(breakdown), key=lambda x: (-x[1].get('percent', 0.0)) * (x[1].get('weight', 1.0) or 1.0))
            # A list of the indices of the dropped scores
            dropped_indices = []
            dropped_breakdown = []
            if drop_count > 0:
                dropped_indices = [x[0] for x in sorted_breakdown[-drop_count:]]
                dropped_breakdown = [x[1] for x in sorted_breakdown[-drop_count:]]

            # Calculate normalized_weight for breakdown
            normalized_weight = 0
            if breakdown:
                normalized_weight = sum((x.get('weight', 1) or 1.0) for x in breakdown)
            if dropped_breakdown:
                normalized_weight -= sum((x.get('weight', 1) or 1.0) for x in dropped_breakdown)

            aggregate_score = 0
            if len(breakdown) > len(dropped_breakdown):
                aggregate_score = sum(m['percent'] * (m.get('weight', 1) or 1.0) for m in breakdown if m not in dropped_breakdown)
            if len(breakdown) - drop_count > 0 and normalized_weight > 0:
                aggregate_score /= normalized_weight
            elif normalized_weight == 0:
                aggregate_score = 1.0
            else:
                assert "Drop count cannot be greater than assignments count."
            return aggregate_score, dropped_indices

        scores = grade_sheet.get(self.type, {}).values()
        unpublished_weights = unpublished_graded_verticals.get(self.type, [])
        breakdown = []
        for i in range(max(self.min_count, len(scores))):
            if i < len(scores) or generate_random_scores:
                if generate_random_scores:  # for debugging!
                    earned = random.randint(2, 15)
                    possible = random.randint(earned, 15)
                    section_name = "Generated"

                else:
                    earned = scores[i].graded_total.earned
                    possible = scores[i].graded_total.possible
                    section_name = scores[i].display_name

                percentage = earned / float(possible)
                weight = getattr(scores[i], 'weight', 1) or 1.0
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
                if i - len(scores) < len(unpublished_weights):
                    weight = unpublished_weights[i - len(scores)]
                else:
                    weight = 1.0
                summary = u"{section_type} {index} Unreleased - 0% (?/?)".format(
                    index=i + self.starting_index,
                    section_type=self.section_type
                )

            short_label = u"{short_label} {index:02d}".format(
                index=i + self.starting_index,
                short_label=self.short_label
            )

            breakdown.append({
                'percent': percentage,
                'label': short_label,
                'detail': summary,
                'category': self.category,
                'weight': weight,
            })

        total_percent, dropped_indices = total_with_drops(breakdown, self.drop_count)

        for dropped_index in dropped_indices:
            breakdown[dropped_index]['mark'] = {
                'detail': u"The lowest {drop_count} {section_type} scores are dropped.".format(
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
            breakdown = [{
                'percent': total_percent,
                'label': total_label,
                'detail': total_detail,
                'category': self.category,
                'prominent': True
            }, ]
        else:
            total_detail = _(u"{section_type} Average = {percent:.0%}").format(
                percent=total_percent,
                section_type=self.section_type
            )
            total_label = _(u"{short_label} Avg").format(short_label=self.short_label)

            if self.show_only_average:
                breakdown = []

            if not self.hide_average:
                breakdown.append({
                    'percent': total_percent,
                    'label': total_label,
                    'detail': total_detail,
                    'category': self.category,
                    'prominent': True
                })

        return {
            'percent': total_percent,
            'section_breakdown': breakdown,
            # No grade_breakdown here
        }
