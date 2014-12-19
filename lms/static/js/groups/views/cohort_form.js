var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortFormView = Backbone.View.extend({
        initialize: function(options) {
            this.template = _.template($('#cohort-form-tpl').text());
            this.contentGroups = options.contentGroups;
        },

        render: function() {
            this.$el.html(this.template({
                cohort: this.model,
                contentGroups: this.contentGroups
            }));
            return this;
        },

        saveForm: function() {
            var self = this,
                showAddError,
                cohortName = this.$('.cohort-create-name').val().trim();
            showAddError = function(message) {
                self.showNotification(
                    {type: 'error', title: message},
                    self.$('.cohort-management-create-form-name label')
                );
            };
            this.removeNotification();
            if (cohortName.length > 0) {
                $.post(
                        this.model.url + '/add',
                    {name: cohortName}
                ).done(function(result) {
                        if (result.success) {
                            self.lastSelectedCohortId = result.cohort.id;
                            self.model.fetch().done(function() {
                                self.showNotification({
                                    type: 'confirmation',
                                    title: interpolate_text(
                                        gettext('The {cohortGroupName} cohort group has been created. You can manually add students to this group below.'),
                                        {cohortGroupName: cohortName}
                                    )
                                });
                            });
                        } else {
                            showAddError(result.msg);
                        }
                    }).fail(function() {
                        showAddError(gettext("We've encountered an error. Please refresh your browser and then try again."));
                    });
            } else {
                showAddError(gettext('Please enter a name for your new cohort group.'));
            }
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text);
