var edx = edx || {};
var onCertificatesReady = null;

(function($, gettext, _) {
    'use strict';

    edx.instructor_dashboard = edx.instructor_dashboard || {};
    edx.instructor_dashboard.certificates = {};

    onCertificatesReady = function() {
        if ($('.certificate-black-list-editor').length > 0) {
            var blackListEl = $('.certificate-black-list-editor');
            var blackListDataUrl = blackListEl.data('url-list');
            var blackListAddUrl = blackListEl.data('url-add');
            var blackListRemoveUrl = blackListEl.data('url-remove');
            var generatedCertsEl = $('.generated-certificates-listing');
            var generatedCertificatesListingUrl = generatedCertsEl.data('url-list');
            var blackListProcess = false;

            function updateBlackListGrid() {
                var gridEl = blackListEl.find('.black-listed-students-grid');
                gridEl.html(gettext('Loading...'));
                $.ajax({
                        type: 'GET',
                        url: blackListDataUrl,
                        cache: false,
                        success: function(res) {
                            if (res.result.length > 0) {
                                var html = '<table><thead>' +
                                    '<tr><th class="user-name">' + gettext('Name') + '</th>' +
                                    '<th class="user-email">' + gettext('Email') + '</th>' +
                                    '<th class="date">' + gettext('Date') + '</th>' +
                                    '<th class="action">' + gettext('Actions') + '</th>' +
                                    '</tr></thead>' +
                                    '<tbody>';
                                $.each(res.result, function(index, value) {
                                    html += '<tr><td>' + value.name + '</td>' +
                                        '<td>' + value.email + '</td>' +
                                        '<td>' + moment(value.created).format('YYYY-MM-DD HH:mm') + '</td>' +
                                        '<td><a href="javascript: void(0)" data-user-id="' + value.user_id + '" class="remove-from-blacklist">' + gettext('Remove') + '</a></td></tr>';
                                });
                                html += '</tbody></table>';
                                gridEl.html(html);
                            } else {
                                gridEl.html('');
                            }
                        }
                });
            }

            function updateGeneratedCertListGrid(page) {
                page = page || 1;
                var gridEl = generatedCertsEl.find('.certificates-listing-grid');
                gridEl.html(gettext('Loading...'));
                $.ajax({
                        type: 'GET',
                        url: generatedCertificatesListingUrl + '?page=' + page,
                        cache: false,
                        success: function(res) {
                            var html = '<table><thead>' +
                                    '<tr><th class="user-email">' + gettext('Email') + '</th>' +
                                    '<th class="date">' + gettext('Date') + '</th>' +
                                    '<th class="grade">' + gettext('Grade') + '</th>' +
                                    '<th class="mode">' + gettext('Mode') + '</th>' +
                                    '<th class="url">' + gettext('URL') + '</th>' +
                                    '</tr></thead>' +
                                    '<tbody>';
                            $.each(res.result, function(index, value) {
                                html += '<tr><td>' + value.email + '</td>' +
                                        '<td>' + moment(value.created).format('YYYY-MM-DD HH:mm') + '</td>' +
                                        '<td>' + value.grade + '</td>' +
                                        '<td>' + value.mode + '</td>' +
                                        '<td><a href="' + value.url +  '" target="_blank">' + gettext('Link') + '</a></td></tr>';
                            });
                            html += '</tbody></table>';
                            html += '<div style="padding-top: 15px; text-align: right;">' + gettext('Pages') + ': ';
                            for (var i = 1; i <= res.pages_count; i++) {
                                if (res.current_page === i) {
                                    html += '<div style="width: 16px; text-align: center; display: inline-block;"><strong>' + i + '</strong></div>';
                                } else {
                                    html += '<div style="width: 16px; text-align: center; display: inline-block;"><a href="javascript: void(0);" class="change-page" data-val="' + i + '">' + i + '</a></div>';
                                }
                            }
                            html += '</div>';
                            gridEl.html(html);
                        }
                });
            }

            blackListEl.find('.add-blacklist').click(function () {
                var userToken = blackListEl.find('.student-username-or-email').val();
                if ((userToken !== '') && (!blackListProcess)) {
                    blackListProcess = true;
                    blackListEl.find('.certificate-blacklist-msg-error').html('');
                    blackListEl.find('.certificate-blacklist-msg-success').html('');
                    $.ajax({
                        type: 'POST',
                        data: {'user': userToken},
                        url: blackListAddUrl,
                        success: function(res) {
                            blackListProcess = false;
                            if (res.success) {
                                blackListEl.find('.certificate-blacklist-msg-success').html(gettext('User was added to blacklist'));
                                blackListEl.find('.student-username-or-email').val('');
                                updateBlackListGrid();
                            } else {
                                blackListEl.find('.certificate-blacklist-msg-error').html(res.message);
                            }
                        }
                    });
                }
            });

            blackListEl.on('click', '.remove-from-blacklist', function() {
                var userId = $(this).data('user-id');
                if (userId && (!blackListProcess)) {
                    blackListProcess = true;
                    $.ajax({
                        type: 'POST',
                        data: {'user_id': userId},
                        url: blackListRemoveUrl,
                        success: function(res) {
                            blackListProcess = false;
                            updateBlackListGrid();
                        }
                    });
                }
            });

            generatedCertsEl.on('click', '.change-page', function() {
                var page = parseInt($(this).data('val'));
                updateGeneratedCertListGrid(page);
            });

            updateBlackListGrid();
            updateGeneratedCertListGrid(1);
        }

        /**
         * Show a confirmation message before letting staff members
         * enable/disable self-generated certificates for a course.
         */
        $('#enable-certificates-form').on('submit', function(event) {
            var isEnabled = $('#certificates-enabled').val() === 'true',
                confirmMessage = '';

            if (isEnabled) {
                confirmMessage = gettext('Allow students to generate certificates for this course?');
            } else {
                confirmMessage = gettext('Prevent students from generating certificates in this course?');
            }

            if (!confirm(confirmMessage)) {
                event.preventDefault();
            }
        });

        /**
         * Refresh the status for example certificate generation
         * by reloading the instructor dashboard.
         */
        $('#refresh-example-certificate-status').on('click', function() {
            window.location.reload();
        });


        /**
         * Start generating certificates for all students.
         */
        var $section = $('section#certificates');
        $section.on('click', '#btn-start-generating-certificates', function(event) {
            if (!confirm(gettext('Start generating certificates for all students in this course?'))) {
                event.preventDefault();
                return;
            }

            var $btn_generating_certs = $(this),
                $certificate_generation_status = $('.certificate-generation-status');
            var url = $btn_generating_certs.data('endpoint');
            $.ajax({
                type: 'POST',
                url: url,
                success: function(data) {
                    $btn_generating_certs.attr('disabled', 'disabled');
                    $certificate_generation_status.text(data.message);
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    $certificate_generation_status.text(gettext('Error while generating certificates. Please try again.'));
                }
            });
        });

        /**
         * Start regenerating certificates for students.
         */
        $section.on('click', '#btn-start-regenerating-certificates', function(event) {
            if (!confirm(gettext('Start regenerating certificates for students in this course?'))) {
                event.preventDefault();
                return;
            }

            var $btn_regenerating_certs = $(this),
                $certificate_regeneration_status = $('.certificate-regeneration-status'),
                url = $btn_regenerating_certs.data('endpoint');

            $.ajax({
                type: 'POST',
                data: $('#certificate-regenerating-form').serializeArray(),
                url: url,
                success: function(data) {
                    $btn_regenerating_certs.attr('disabled', 'disabled');
                    if (data.success) {
                        $certificate_regeneration_status.text(data.message).addClass('message');
                    } else {
                        $certificate_regeneration_status.text(data.message).addClass('message');
                    }
                },
                error: function(jqXHR) {
                    try {
                        var response = JSON.parse(jqXHR.responseText);
                        $certificate_regeneration_status.text(gettext(response.message)).addClass('message');
                    } catch (error) {
                        $certificate_regeneration_status.
                            text(gettext('Error while regenerating certificates. Please try again.')).
                            addClass('message');
                    }
                }
            });
        });
    };

    // Call onCertificatesReady on document.ready event
    $(onCertificatesReady);

    var Certificates = (function() {
        function Certificates($section) {
            $section.data('wrapper', this);
            if ($(this.$section).length > 0) {
                this.instructor_tasks = new window.InstructorDashboard.util.PendingInstructorTasks($section);
            }
        }

        Certificates.prototype.onClickTitle = function() {
            if (this.instructor_tasks) {
                return this.instructor_tasks.task_poller.start();
            }
        };

        Certificates.prototype.onExit = function() {
            return this.instructor_tasks.task_poller.stop();
        };
        return Certificates;
    }());

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        Certificates: Certificates
    });
}($, gettext, _));
