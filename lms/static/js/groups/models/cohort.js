var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CohortModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            name: '',
            user_count: 0
        }
    });
}).call(this, Backbone);
