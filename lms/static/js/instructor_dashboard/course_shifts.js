/* globals _ */

(function(gettext, _) {
    'use strict';

    var CourseShifts = (function() {
        function CourseShifts($section) {
            this.$el = $section;
            var block = this.$el.find('.course-shifts');

            this.$el.data('wrapper', this);
            this.initialized = false;
            this.userId = null;
            this.usersCurrentShift = {};

            this.courseShifts = [];
            this.listCourseShiftsUrl = $(block).data('get-course-shifts-url');
            this.updateCourseShiftsUrl = $(block).data('update-course-shifts-url');
            this.findUserAndCourseShiftsUrl = $(block).data('find-user-and-course-shifts-url');
            this.updateUserCourseShiftUrl = $(block).data('update-user-course-shift-url');

            this.currentUserTZname = moment.tz(moment.tz.guess()).format('z');

            this.$el.find('.search-user-and-shift').on("click", $.proxy(this, "searchUser"));
            this.$el.find('.change-user-shift').on("click", $.proxy(this, "updateUser"));
        }

        CourseShifts.prototype.onClickTitle = function() {
            if (!this.initialized) {
                this.initialized = true;
                this.refreshCourseShifts();
            }
        };

        CourseShifts.prototype.addCreateBlock = function() {
            this.showShiftLine(null, true, {
                name: '',
                startDate: '',
                startTime: '',
                enrollStartDate: '',
                enrollStartTime: '',
                enrollEndDate: '',
                enrollEndTime: '',
                numberOfStudents: 0,
                studioVersion: false,
                id: 'new' + Date.now()
            });
        };

        CourseShifts.prototype.refreshCourseShifts = function() {
            this.$el.find('.list-shifts').empty();
            var self = this;
            this.fetchShifts(function() {
                self.$el.find('.list-shifts').append(self.getTableHeader());
                $.each(self.courseShifts, function(index, value) {
                    self.showShiftLine(null, false, value);
                });
                self.addCreateBlock();
            });
        };

        CourseShifts.prototype.refreshUserShiftSelector = function() {
            var self = this;
            var options = [];
            var actionsBlock = this.$el.find('.user-actions');
            var selector = this.$el.find('#user-shift-selector');

            if (!this.userId) {
                $(actionsBlock).hide();
                return;
            }

            $.each(this.courseShifts, function(index, value) {
                if (value.id !== self.usersCurrentShift.id) {
                    options.push({
                        id: value.id,
                        name: value.name
                    });
                }
            });

            if (options.length > 0) {
                $(actionsBlock).show();
                options = _.sortBy(options, 'name');
                $(selector).html('');
                $.each(options, function(index, value) {
                    var o = $('<option/>', { value: value.id })
                            .text(value.name);
                    $(selector).append(o);
                });
            } else {
                $(actionsBlock).hide();
                return;
            }
        };

        CourseShifts.prototype.getTableHeader = function() {
            return '<tr> \
                <th class="header title-field">' + gettext("Title") + '</th> \
                <th class="header date-field">' + gettext("Start Date") + ' (' + this.currentUserTZname + ')</th> \
                <th class="header date-field">' + gettext("Enrollment Start Date") + ' (' + this.currentUserTZname + ')</th> \
                <th class="header date-field">' + gettext("Enrollment End Date") + ' (' + this.currentUserTZname + ')</th> \
                <th class="header students-num">' + gettext("Number of Students") + '</th> \
                <th class="header actions">' + gettext("Actions") + '</th> \
                </tr>';
        };

        CourseShifts.prototype.getItemTpl = function(studioVersion) {
            var btn = '';
            if (!studioVersion) {
                btn = '<button type="button" class="edit-item-%id" data-id="%id">' + gettext("Edit") + '</button>';
            } else {
                btn = gettext("Studio version");
            }
            return '<tr class="field-group field-group-course-start block-%id"> \
                        <td class="field title-field"> \
                          <div>%title</div> \
                        </td> \
                        <td class="field date-field"> \
                          <div>%startDate %startTime</div> \
                        </td> \
                        <td class="field date-field"> \
                          <div>%enrollStartDate %enrollStartTime</div> \
                        </td>\
                        <td class="field date-field"> \
                          <div>%enrollEndDate %enrollEndTime</div> \
                        </td> \
                        <td class="field students-num"> \
                          <div>%numberOfStudents</div> \
                        </td> \
                        <td class="field actions">' + btn + '</td> \
                    </tr>';
        };

        CourseShifts.prototype.getEditItemTpl = function(showCancel) {
            var tplCancel = '';
            if (showCancel) {
                tplCancel = '<button type="button" class="cancel-item-%id" data-id="%id">' + gettext("Cancel") + '</button>&nbsp;';
            }
            return '<tr class="field-group field-group-course-start block-%id"> \
                       <td class="field title-field"> \
                          <input class="input-title-field" type="text" value="%title" id="title-%id" maxlength="20" autocomplete="off">\
                       </td> \
                       <td class="field date-field"> \
                          <input type="text" id="start-date-%id" class="start-date date"\
                                 placeholder="YYYY-MM-DD" autocomplete="off" value="%startDate"> \
                          <input type="text" id="start-time-%id" class="start-time time" \
                                 placeholder="HH:MM" autocomplete="off" value="%startTime"> \
                       </td> \
                       <td class="field date-field"> \
                          <input type="text" id="enroll-start-date-%id" class="enroll-start-date date"\
                                 placeholder="YYYY-MM-DD" autocomplete="off" value="%enrollStartDate"> \
                          <input type="text" id="enroll-start-time-%id" class="enroll-start-time time" \
                                 placeholder="HH:MM" autocomplete="off" value="%enrollStartTime"> \
                       </td> \
                       <td class="field date-field"> \
                          <input type="text" id="enroll-end-date-%id" class="enroll-end-date date"\
                                 placeholder="YYYY-MM-DD" autocomplete="off" value="%enrollEndDate"> \
                          <input type="text" id="enroll-end-time-%id" class="enroll-end-time time" \
                                 placeholder="HH:MM" autocomplete="off" value="%enrollEndTime"> \
                       </td> \
                       <td class="field students-num"> \
                           %numberOfStudents \
                       </td> \
                       <td class="field actions"> \
                            ' + tplCancel + '<button type="button" class="save-item-%id" data-id="%id">' + gettext("Save") + '</button> \
                       </td> \
                    </tr>\
                    <tr class="error-msg-tr-%id">\
                       <td colspan="6" class="error-msg error-msg-%id"></td> \
                    </tr>';
        };

        CourseShifts.prototype.blockInterface = function() {
            this.$el.find('button').attr('disabled', 'disabled');
        };

        CourseShifts.prototype.unblockInterface = function() {
            this.$el.find('button').removeAttr('disabled');
        };

        CourseShifts.prototype.prepareShift = function(value) {
            var startDate = moment.utc(value.start_date, "YYYY-MM-DD HH:mm").local();
            var enrollStartDate = moment.utc(value.enrollment_start_date, "YYYY-MM-DD HH:mm").local();
            var enrollEndDate = moment.utc(value.enrollment_end_date, "YYYY-MM-DD HH:mm").local();

            return {
                id: value.id,
                name: value.name,
                startDate: startDate.format("YYYY-MM-DD"),
                startTime: startDate.format("HH:mm"),
                enrollStartDate: enrollStartDate.format("YYYY-MM-DD"),
                enrollStartTime: enrollStartDate.format("HH:mm"),
                enrollEndDate: enrollEndDate.format("YYYY-MM-DD"),
                enrollEndTime: enrollEndDate.format("HH:mm"),
                numberOfStudents: value.number_of_students,
                studioVersion: value.studio_version
            };
        };

        CourseShifts.prototype.fetchShifts = function(onSuccess) {
            var self = this;
            this.$el.find('.main-block').hide();
            this.$el.find('.loading').show();
            $.ajax({
                type: 'GET',
                url: this.listCourseShiftsUrl,
                dataType : "json"
            }).success(function(response) {
                self.courseShifts = [];
                if (response.success) {
                    $.each(response.data, function(index, value) {
                        self.courseShifts.push(self.prepareShift(value));
                    });
                    onSuccess();
                }
            }).error(function() {
                self.courseShifts = [];
            }).complete(function() {
                self.$el.find('.loading').hide();
                self.$el.find('.main-block').show();
            });
        };

        CourseShifts.prototype.getShift = function(id) {
            id = parseInt(id);
            var item = null;
            $.each(this.courseShifts, function(index, value) {
                if (value.id === id) {
                    item = value;
                }
            });
            return item;
        };

        CourseShifts.prototype.addToStorage = function(newItem) {
            this.courseShifts.push(newItem);
        };

        CourseShifts.prototype.updateStorage = function(newItem) {
            var newShifts = [];
            $.each(this.courseShifts, function(idx, value) {
                if (value.id !== newItem.id) {
                    newShifts.push(value);
                } else {
                    newShifts.push(newItem);
                }
            });
            this.courseShifts = newShifts;
        };

        CourseShifts.prototype.removeFromStorage = function(id) {
            id = parseInt(id);
            var newShifts = [];
            $.each(this.courseShifts, function(index, value) {
                if (value.id !== id) {
                    newShifts.push(value);
                }
            });
            this.courseShifts = newShifts;
        };

        CourseShifts.prototype.showShiftLine = function(replaceId, editMode, value) {
            var tpl = '';
            if (editMode) {
                tpl = this.getEditItemTpl(replaceId !== null && editMode);
            } else {
                this.removeErrorBlock(value.id);
                tpl = this.getItemTpl(value.studioVersion);
            }

            tpl = tpl.replace(/%title/g, value.name)
                .replace(/%startDate/g, value.startDate)
                .replace(/%startTime/g, value.startTime)
                .replace(/%enrollStartDate/g, value.enrollStartDate)
                .replace(/%enrollStartTime/g, value.enrollStartTime)
                .replace(/%enrollEndDate/g, value.enrollEndDate)
                .replace(/%enrollEndTime/g, value.enrollEndTime)
                .replace(/%numberOfStudents/g, value.numberOfStudents)
                .replace(/%id/g, value.id);

            if (replaceId === null) {
                this.$el.find('.list-shifts').append(tpl);
            } else {
                this.$el.find('.block-' + replaceId).replaceWith(tpl);
            }

            if (editMode) {
                this.$el.find('#start-date-' + value.id).datepicker({'dateFormat': 'yy-mm-dd'});
                this.$el.find('#enroll-start-date-' + value.id).datepicker({'dateFormat': 'yy-mm-dd'});
                this.$el.find('#enroll-end-date-' + value.id).datepicker({'dateFormat': 'yy-mm-dd'});
                this.$el.find('#start-time-' + value.id).timepicker({step: 30, timeFormat: 'H:i'});
                this.$el.find('#enroll-start-time-' + value.id).timepicker({step: 30, timeFormat: 'H:i'});
                this.$el.find('#enroll-end-time-' + value.id).timepicker({step: 30, timeFormat: 'H:i'});
                this.$el.find('.save-item-' + value.id).on("click", $.proxy(this, "saveShift"));
                if (replaceId !== null) {
                    this.$el.find('.cancel-item-' + value.id).on("click", $.proxy(this, "cancelShift"));
                }
            } else {
                this.$el.find('.edit-item-' + value.id).on("click", $.proxy(this, "editShift"));
            }
        };

        CourseShifts.prototype.editShift = function(e) {
            var id = parseInt($(e.currentTarget).data('id'));
            var item = this.getShift(id);
            this.showShiftLine(id, true, item);
        };

        CourseShifts.prototype.showErrorMessage = function(id, text) {
            this.$el.find('.error-msg-' + id).html(text);
        };

        CourseShifts.prototype.cancelShift = function(e) {
            var id = parseInt($(e.currentTarget).data('id'));
            var item = this.getShift(id);
            this.showShiftLine(id, false, item);
        };

        CourseShifts.prototype.removeErrorBlock = function(id) {
            this.$el.find(".error-msg-tr-" + id).remove();
        };

        CourseShifts.prototype.saveShift = function(e) {
            var id = $(e.currentTarget).data('id').toString();
            var title = this.$el.find('#title-' + id).val();

            var startDate = this.$el.find('#start-date-' + id).val();
            var startTime = this.$el.find('#start-time-' + id).val();
            var startDateTime = startDate + ' ' + startTime;
            var startDt = moment(startDateTime, 'YYYY-MM-DD HH:mm');

            var enrollStartDate = this.$el.find('#enroll-start-date-' + id).val();
            var enrollStartTime = this.$el.find('#enroll-start-time-' + id).val();
            var enrollStartDateTime = enrollStartDate + ' ' + enrollStartTime;
            var enrollStartDt = moment(enrollStartDateTime, 'YYYY-MM-DD HH:mm');

            var enrollEndDate = this.$el.find('#enroll-end-date-' + id).val();
            var enrollEndTime = this.$el.find('#enroll-end-time-' + id).val();
            var enrollEndDateTime = enrollEndDate + ' ' + enrollEndTime;
            var enrollEndDt = moment(enrollEndDateTime, 'YYYY-MM-DD HH:mm');

            var isNew = id.indexOf('new') === 0;
            var self = this;

            this.showErrorMessage(id, "");

            if (!title) {
                this.showErrorMessage(id, gettext("Name field can't be empty"));
                return false;
            }

            if (!startDate) {
                this.showErrorMessage(id, gettext("Start date field can't be empty"));
                return false;
            }

            if (!startTime) {
                this.showErrorMessage(id, gettext("Start time field can't be empty"));
                return false;
            }

            if (!enrollStartDate) {
                this.showErrorMessage(id, gettext("Enrollment start date field can't be empty"));
                return false;
            }

            if (!enrollStartTime) {
                this.showErrorMessage(id, gettext("Enrollment start time field can't be empty"));
                return false;
            }

            if (!enrollEndDate) {
                this.showErrorMessage(id, gettext("Enrollment end date field can't be empty"));
                return false;
            }

            if (!enrollEndTime) {
                this.showErrorMessage(id, gettext("Enrollment end time field can't be empty"));
                return false;
            }

            if (!enrollEndDt.isAfter(enrollStartDt)) {
                this.showErrorMessage(id, gettext("Enrollment end date must be after the start date"));
                return false;
            }

            if (!startDt.isAfter(enrollStartDt)) {
                this.showErrorMessage(id, gettext("Start date must be later than the enrollment start date"));
                return false;
            }

            this.$el.find('.save-item-' + id).text(gettext("Saving..."));

            var item = {
                title: title,
                startDate: startDt.utc().format("YYYY-MM-DD HH:mm"),
                enrollStartDate: enrollStartDt.utc().format("YYYY-MM-DD HH:mm"),
                enrollEndDate: enrollEndDt.utc().format("YYYY-MM-DD HH:mm")
            };

            if (!isNew) {
                item.id = id;
            }

            this.blockInterface();

            $.ajax({
                type: 'POST',
                url: this.updateCourseShiftsUrl,
                contentType: 'application/json',
                dataType : "json",
                data: JSON.stringify(item)
            }).success(function(response) {
                if (response.success) {
                    var shift = self.prepareShift(response.shift);
                    if (isNew) {
                        self.addToStorage(shift);
                        self.addCreateBlock();
                    } else {
                        self.updateStorage(shift);
                    }
                    self.showShiftLine(id, false, shift);
                    self.refreshUserShiftSelector();
                } else {
                    self.showErrorMessage(id, response.errorMessage);
                    self.$el.find('.save-item-' + id).text(gettext("Save"));
                }
            }).error(function () {
                self.$el.find('.save-item-' + id).text(gettext("Save"));
                self.showErrorMessage(id, gettext("Server error."));
            }).complete(function() {
                self.unblockInterface();
            });
        };

        CourseShifts.prototype.searchUser = function() {
            var self = this;
            var userSearchToken = this.$el.find('#user-search-token').val();
            var errorBlock = this.$el.find('.user-search-error');
            var updateUserErrorBlock = this.$el.find('.user-update-error');
            var actionsBlock = this.$el.find('.user-actions');
            var userInfoBlock = this.$el.find('.user-info');

            if (!userSearchToken) {
                return;
            }

            this.blockInterface();
            $(userInfoBlock).html('');
            $(errorBlock).html('');
            $(updateUserErrorBlock).html('');
            $(actionsBlock).hide();

            $.ajax({
                type: 'GET',
                url: this.findUserAndCourseShiftsUrl + '?word=' + encodeURIComponent(userSearchToken),
                dataType : "json"
            }).success(function(response) {
                if (response.success) {
                    self.userId = response.userid;
                    if (response.shift) {
                        self.usersCurrentShift = response.shift;
                    }
                    var userShift = (self.usersCurrentShift.name) ? self.usersCurrentShift.name : '-';
                    $(userInfoBlock).html(gettext("User was found. User's shift is: ") + userShift);
                    self.refreshUserShiftSelector();
                } else {
                    $(errorBlock).html(response.errorMessage);
                }
            }).error(function () {
                $(errorBlock).html(gettext('Server error.'));
            }).complete(function() {
                self.unblockInterface();
            });
        };

        CourseShifts.prototype.updateUser = function() {
            var self = this;
            var updateUserErrorBlock = this.$el.find('.user-update-error');
            var userInfoBlock = this.$el.find('.user-info');
            var actionsBlock = this.$el.find('.user-actions');

            var shiftId = this.$el.find('#user-shift-selector').val();
            if (!shiftId) {
                return;
            }

            var data = {
                course_shift_id: parseInt(shiftId),
                user_id: this.userId
            };

            this.blockInterface();
            $(updateUserErrorBlock).html('');

            $.ajax({
                type: 'POST',
                url: this.updateUserCourseShiftUrl,
                contentType: 'application/json',
                dataType : "json",
                data: JSON.stringify(data)
            }).success(function(response) {
                if (response.success) {
                    $(userInfoBlock).html('');
                    $(actionsBlock).hide();
                    self.$el.find('#user-search-token').val('');
                    self.userId = null;
                    self.usersCurrentShift = {};
                    self.refreshCourseShifts();
                    alert(gettext("User was successfully updated"));
                } else {
                    $(updateUserErrorBlock).html(response.errorMessage);
                }
            }).error(function () {
                $(updateUserErrorBlock).html(gettext('Server error.'));
            }).complete(function() {
                self.unblockInterface();
            });

        };

        return CourseShifts;
    }());

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        CourseShifts: CourseShifts
    });

    this.CourseShifts = CourseShifts;
}).call(this, gettext, _);
