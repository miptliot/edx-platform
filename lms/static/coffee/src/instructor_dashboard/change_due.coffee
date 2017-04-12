###
Change Due Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

# Load utilities
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks

# A typical section object.
# constructed with $section, a jquery object
# which holds the section body container.
class ChangeDue
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # gather elements
    @instructor_tasks = new (PendingInstructorTasks()) @$section

  # handler for when the section title is clicked.
  onClickTitle: -> @instructor_tasks.task_poller.start()

  # handler for when the section is closed
  onExit: -> @instructor_tasks.task_poller.stop()


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  ChangeDue: ChangeDue
