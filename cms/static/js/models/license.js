define(["backbone"], function(Backbone) {
    /**
     * Simple model for an asset.
     */
    var License = Backbone.Model.extend({
        defaults: {
            license: "NONE",
            version: ""
        },

        set: function(attributes, options) {
            if (options) {
                options.validate = true;
            }
            else {
                options = {
                    validate: true
                };
            }
            Backbone.Model.prototype.set.call(this, attributes, options);
        },

        validate: function(newattrs) {
            var errors = {};
            if (newattrs.license instanceof String) {
                var license, validLicense;
                license = newattrs.license;

                if (license == "ARR" || license == "CC0") {
                    validLicense = license;
                }
                else {
                    var attr = license.split("-");

                    if (attr.length > 1 && attr[0] == "CC" && attr[1] == "BY") {
                        validLicense = attr.join("-");
                    }
                    else {
                        validLicense = "NONE";
                    }
                }

                newattrs.license = validLicense;
            }
            else {
                newattrs.license = "NONE";
            }
            if (!_.isEmpty(errors)) return errors;
            // NOTE don't return empty errors as that will be interpreted as an error state
        },
    });
    return License;
});
