var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text, CohortModel) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortFormView = Backbone.View.extend({
        events : {
            'change .field-radio input': 'onRadioButtonChange',
            'click .tab-content-settings .action-save': 'saveSettings',
            'submit .cohort-management-group-add-form': 'addStudents'
        },

        initialize: function(options) {
            this.template = _.template($('#cohort-form-tpl').text());
            this.cohortUserPartitionId = options.cohortUserPartitionId;
            this.contentGroups = options.contentGroups;
        },

        render: function() {
            this.$el.html(this.template({
                cohort: this.model,
                contentGroups: this.contentGroups
            }));
            return this;
        },

        onRadioButtonChange: function(event) {
            var target = $(event.currentTarget),
                groupsEnabled = target.val() === 'yes';
            this.$('.input-cohort-group-association').toggleClass('is-disabled', !groupsEnabled);
        },

        getSelectedGroupId: function() {
            if (!this.$('.radio-yes').prop('checked')) {
                return null;
            }
            return parseInt(this.$('.input-cohort-group-association').val());
        },

        saveForm: function() {
            var cohort = this.model,
                cohortName = this.$('.cohort-create-name').val().trim(),
                groupId = this.getSelectedGroupId(),
                saveOperation = $.Deferred();
            if (cohortName.length > 0) {
                cohort.save(
                    {name: cohortName, user_partition_id: this.cohortUserPartitionId, group_id: groupId}
                ).done(function(result) {
                    if (!result.error) {
                        cohort.id = result.id;
                        saveOperation.resolve();
                    } else {
                        saveOperation.reject(result.error);
                    }
                }).fail(function() {
                    saveOperation.reject(gettext("We've encountered an error. Please refresh your browser and then try again."));
                });
            } else {
                saveOperation.reject(gettext('Please enter a name for your new cohort group.'));
            }
            return saveOperation.promise();
        }
    });
}).call(this, $, _, Backbone, gettext, interpolate_text, edx.groups.CohortModel);
