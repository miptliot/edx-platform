/* globals _, SendEmail */

(function() {
    'use strict';
    var KeywordValidator, PendingInstructorTasks,
        createEmailContentTable, createEmailDelayContentTable, createEmailMessageViews, createTaskListTable,
        plantTimeout, statusAjaxError;

    plantTimeout = function() {
        return window.InstructorDashboard.util.plantTimeout.apply(this, arguments);
    };

    statusAjaxError = function() {
        return window.InstructorDashboard.util.statusAjaxError.apply(this, arguments);
    };

    PendingInstructorTasks = function() {
        return window.InstructorDashboard.util.PendingInstructorTasks;
    };

    createTaskListTable = function() {
        return window.InstructorDashboard.util.createTaskListTable.apply(this, arguments);
    };

    createEmailContentTable = function() {
        return window.InstructorDashboard.util.createEmailContentTable.apply(this, arguments);
    };

    createEmailDelayContentTable = function() {
        return window.InstructorDashboard.util.createEmailDelayContentTable.apply(this, arguments);
    };

    createEmailMessageViews = function() {
        return window.InstructorDashboard.util.createEmailMessageViews.apply(this, arguments);
    };

    KeywordValidator = function() {
        return window.InstructorDashboard.util.KeywordValidator;
    };

    this.SendEmail = (function() {
        function SendEmail($container) {
            var sendemail = this;
            this.$container = $container;
            this.$emailEditor = XBlock.initializeBlock($('.xblock-studio_view'));
            this.$send_to = this.$container.find("input[name='send_to']");
            this.$cohort_targets = this.$send_to.filter('[value^="cohort:"]');
            this.$course_mode_targets = this.$send_to.filter('[value^="track:"]');
            this.$subject = this.$container.find("input[name='subject']");
            this.$checkbox_send_in_future = this.$container.find("input[name='send_in_future']");
            this.$datetime_when_to_send = this.$container.find(".datetime_when_to_send");
            this.$date_when_to_send = this.$container.find("input[name='date_when_to_send']");
            this.$time_when_to_send = this.$container.find("input[name='time_when_to_send']");
            this.$btn_send = this.$container.find("input[name='send']");
            this.$task_response = this.$container.find('.request-response');
            this.$request_response_error = this.$container.find('.request-response-error');
            this.$content_request_response_error = this.$container.find('.content-request-response-error');
            this.$scheduled_request_response_error = this.$container.find('.scheduled-request-response-error');
            this.$history_request_response_error = this.$container.find('.history-request-response-error');
            this.$btn_task_history_email = this.$container.find("input[name='task-history-email']");
            this.$btn_task_history_email_content = this.$container.find("input[name='task-history-email-content']");
            this.$btn_scheduled_emails = this.$container.find("input[name='scheduled-emails-content']");
            this.$table_task_history_email = this.$container.find('.task-history-email-table');
            this.$table_email_content_history = this.$container.find('.content-history-email-table');
            this.$table_scheduled_email_table = this.$container.find('.content-scheduled-email-table');
            this.$email_content_table_inner = this.$container.find('.content-history-table-inner');
            this.$email_content_scheduled_table_inner = this.$container.find('.content-scheduled-table-inner');
            this.$email_messages_wrapper = this.$container.find('.email-messages-wrapper');
            this.$checkbox_send_in_future.click(function() {
                if($(this).is(":checked")) {
                    $(sendemail.$datetime_when_to_send).removeClass('hidden');
                } else {
                    $(sendemail.$datetime_when_to_send).addClass('hidden');
                }
            });
            $(this.$date_when_to_send).datepicker({
                minDate: 0,
                dateFormat: 'dd.mm.yy'
            });
            $(this.$time_when_to_send).timepicker({
                step: 60,
                timeFormat: 'H:i'
            });
            this.$btn_send.click(function() {
                var body, confirmMessage, displayTarget, fullConfirmMessage, message,
                    sendData, subject, successMessage, target, targets, validation, i, len;
                subject = sendemail.$subject.val();
                body = sendemail.$emailEditor.save().data;
                targets = [];
                sendemail.$send_to.filter(':checked').each(function() {
                    return targets.push(this.value);
                });

                var dateToSendVal = '';
                var timeToSendVal = '';
                var dtSendVal = '';
                var sentInFuture = '';

                if ($(sendemail.$checkbox_send_in_future).is(":checked")) {
                    dateToSendVal = $(sendemail.$date_when_to_send).val();
                    var dateToSend = moment(dateToSendVal, 'DD-MM-YYYY');

                    timeToSendVal = $(sendemail.$time_when_to_send).val();
                    var timeToSend = moment(timeToSendVal, 'HH:mm');

                    dtSendVal = dateToSendVal + ' ' + timeToSendVal;
                    var dtSend = moment(dtSendVal, 'DD-MM-YYYY HH:mm');

                    if (!dateToSend.isValid()) {
                        return alert(gettext('Chosen date is invalid'));  // eslint-disable-line no-alert
                    }
                    if (!timeToSend.isValid()) {
                        return alert(gettext('Chosen time is invalid'));  // eslint-disable-line no-alert
                    }
                    if (moment(new Date()).isAfter(dtSend)) {
                        return alert(gettext("Date and time can't be before the current moment"));  // eslint-disable-line no-alert
                    }

                    sentInFuture = dtSend.diff(moment(new Date()));
                    sentInFuture = parseInt(sentInFuture / 1000);   // seconds
                }
                if (subject === '') {
                    return alert(gettext('Your message must have a subject.'));  // eslint-disable-line no-alert
                } else if (body === '') {
                    return alert(gettext('Your message cannot be blank.'));  // eslint-disable-line no-alert
                } else if (targets.length === 0) {
                    return alert(gettext( // eslint-disable-line no-alert
                        'Your message must have at least one target.'));
                } else {
                    validation = KeywordValidator().validate_string(body);
                    if (!validation.isValid) {
                        message = gettext(
                            'There are invalid keywords in your email. Check the following keywords and try again.');
                        message += '\n' + validation.invalidKeywords.join('\n');
                        alert(message);  // eslint-disable-line no-alert
                        return false;
                    }
                    displayTarget = function(value) {
                        if (value === 'myself') {
                            return gettext('Yourself');
                        } else if (value === 'staff') {
                            return gettext('Everyone who has staff privileges in this course');
                        } else if (value === 'learners') {
                            return gettext('All learners who are enrolled in this course');
                        } else if (value.startsWith('cohort')) {
                            return gettext('All learners in the {cohort_name} cohort')
                                .replace('{cohort_name}', value.slice(value.indexOf(':') + 1));
                        } else if (value.startsWith('track')) {
                            return gettext('All learners in the {track_name} track')
                                .replace('{track_name}', value.slice(value.indexOf(':') + 1));
                        }
                    };
                    successMessage = gettext('Your email message was successfully queued for sending. In courses with a large number of learners, email messages to learners might take up to an hour to be sent.');  // eslint-disable-line max-len
                    confirmMessage = gettext(
                        'You are sending an email message with the subject {subject} to the following recipients.');
                    for (i = 0, len = targets.length; i < len; i++) {
                        target = targets[i];
                        confirmMessage += '\n-' + displayTarget(target);
                    }
                    confirmMessage += '\n\n' + gettext('Is this OK?');
                    fullConfirmMessage = confirmMessage.replace('{subject}', subject);
                    if (confirm(fullConfirmMessage)) {  // eslint-disable-line no-alert
                        sendData = {
                            action: 'send',
                            send_to: JSON.stringify(targets),
                            subject: subject,
                            message: body,
                            send_in_future: sentInFuture
                        };
                        return $.ajax({
                            type: 'POST',
                            dataType: 'json',
                            url: sendemail.$btn_send.data('endpoint'),
                            data: sendData,
                            success: function() {
                                return sendemail.display_response(successMessage);
                            },
                            error: statusAjaxError(function() {
                                return sendemail.fail_with_error(gettext('Error sending email.'));
                            })
                        });
                    } else {
                        sendemail.task_response.empty();
                        return sendemail.$request_response_error.empty();
                    }
                }
            });
            this.$btn_task_history_email.click(function() {
                var url = sendemail.$btn_task_history_email.data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    success: function(data) {
                        if (data.tasks.length) {
                            return createTaskListTable(sendemail.$table_task_history_email, data.tasks);
                        } else {
                            sendemail.$history_request_response_error.text(
                                gettext('There is no email history for this course.')
                            );
                            return sendemail.$history_request_response_error.css({
                                display: 'block'
                            });
                        }
                    },
                    error: statusAjaxError(function() {
                        return sendemail.$history_request_response_error.text(
                            gettext('There was an error obtaining email task history for this course.')
                        );
                    })
                });
            });
            var getScheduledEmails = function() {
                var url = sendemail.$btn_scheduled_emails.data('endpoint');
                var removeUrl = sendemail.$btn_scheduled_emails.data('remove-endpoint');
                sendemail.$scheduled_request_response_error.css({display: 'none'});
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    success: function(data) {
                        if (data.emails.length) {
                            createEmailDelayContentTable(sendemail.$table_scheduled_email_table,
                                sendemail.$email_content_scheduled_table_inner, data.emails
                            );
                            sendemail.$container.find('.email_remove_link').each(function(idx, obj) {
                                var clickSet = $(obj).attr('clickSet');
                                if (!clickSet) {
                                    $(obj).attr('clickSet', '1');
                                    $(obj).click(function() {
                                        if (confirm(gettext("Remove scheduled email?"))) {
                                            $.ajax({
                                                type: 'POST',
                                                dataType: 'json',
                                                url: removeUrl,
                                                data: {
                                                    'msg-id': $(obj).data('msg-id')
                                                },
                                                success: function(data) {
                                                    if (data.success) {
                                                        getScheduledEmails();
                                                    } else {
                                                        alert(data.error);
                                                    }
                                                },
                                                error: function() {
                                                    alert(gettext("Something wrong. Can't remove email"));
                                                }
                                            });
                                        }
                                    });
                                }
                            });
                            return createEmailMessageViews(sendemail.$email_messages_wrapper, data.emails);
                        } else {
                            sendemail.$scheduled_request_response_error.text(
                                gettext("There is no scheduled emails for this course.")
                            );
                            return sendemail.$scheduled_request_response_error.css({
                                display: 'block'
                            });
                        }
                    },
                    error: statusAjaxError(function() {
                        sendemail.$scheduled_request_response_error.text(
                            gettext("There was an error obtaining scheduled emails for this course.")
                        );
                        return sendemail.$scheduled_request_response_error.css({
                            display: 'block'
                        });
                    })
                });
            };
            this.$btn_scheduled_emails.click(getScheduledEmails);
            this.$btn_task_history_email_content.click(function() {
                var url = sendemail.$btn_task_history_email_content.data('endpoint');
                return $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: url,
                    success: function(data) {
                        if (data.emails.length) {
                            createEmailContentTable(sendemail.$table_email_content_history,
                                sendemail.$email_content_table_inner, data.emails
                            );
                            return createEmailMessageViews(sendemail.$email_messages_wrapper, data.emails);
                        } else {
                            sendemail.$content_request_response_error.text(
                                gettext('There is no email history for this course.')
                            );
                            return sendemail.$content_request_response_error.css({
                                display: 'block'
                            });
                        }
                    },
                    error: statusAjaxError(function() {
                        return sendemail.$content_request_response_error.text(
                            gettext('There was an error obtaining email content history for this course.')
                        );
                    })
                });
            });
            this.$send_to.change(function() {
                var targets;
                var inputDisable = function() {
                    this.checked = false;
                    this.disabled = true;
                    return true;
                };
                var inputEnable = function() {
                    this.disabled = false;
                    return true;
                };
                if ($('input#target_learners:checked').length) {
                    sendemail.$cohort_targets.each(inputDisable);
                    sendemail.$course_mode_targets.each(inputDisable);
                } else {
                    sendemail.$cohort_targets.each(inputEnable);
                    sendemail.$course_mode_targets.each(inputEnable);
                }
                targets = [];
                $('input[name="send_to"]:checked+label').each(function() {
                    return targets.push(this.innerText.replace(/\s*\n.*/g, ''));
                });
                return $('.send_to_list').text(gettext('Send to:') + ' ' + targets.join(', '));
            });
        }

        SendEmail.prototype.fail_with_error = function(msg) {
            this.$task_response.empty();
            this.$request_response_error.empty();
            this.$request_response_error.text(msg);
            return $('.msg-confirm').css({
                display: 'none'
            });
        };

        SendEmail.prototype.display_response = function(dataFromServer) {
            this.$task_response.empty();
            this.$request_response_error.empty();
            this.$task_response.text(dataFromServer);
            return $('.msg-confirm').css({
                display: 'block'
            });
        };

        return SendEmail;
    }());

    this.Email = (function() {
        function email($section) {
            var eml = this;
            this.$section = $section;
            this.$section.data('wrapper', this);
            plantTimeout(0, function() {
                return new SendEmail(eml.$section.find('.send-email'));
            });
            if ($(this.$section).length > 0) {
                this.instructor_tasks = new (PendingInstructorTasks())(this.$section);
            }
        }

        email.prototype.onClickTitle = function() {
            return this.instructor_tasks.task_poller.start();
        };

        email.prototype.onExit = function() {
            return this.instructor_tasks.task_poller.stop();
        };

        return email;
    }());

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        Email: this.Email
    });
}).call(this);
