define(["js/views/baseview", "underscore", "gettext", "js/models/license"],
    function(BaseView, _, gettext, LicenseModel) {

        var LicenseView = BaseView.extend({
            initialize: function(options) {
                if (!this.model) {
                    this.model = new LicenseModel();
                }
                else if (!(this.model instanceof LicenseModel)) {
                    this.model = new LicenseModel({license: this.model.get('license')});
                }

                // Rerender on model change
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                this.$el.html(this.renderLicense());

                return this;
            },

            renderLicense: function() {
                var license, licenseHtml, licenseText, licenseLink, licenseTooltip;
                license = (this.model.get('license') || "NONE");

                if(license === "NONE" || license === "ARR"){
                    // All rights reserved
                    licenseText = gettext("All rights reserved")
                    return "<span class='license-icon license-arr'></span><span class='license-text'>" + licenseText + "</span>";
                }
                else if(license === "CC0"){
                    // Creative commons zero license
                    licenseText = gettext("No rights reserved")
                    return "<a rel='license' href='http://creativecommons.org/publicdomain/zero/1.0/' target='_blank'><span class='license-icon license-cc0'></span><span class='license-text'>" + licenseText + "</span></a>";
                }
                else {
                    // Creative commons license
                    licenseVersion = "4.0";
                    licenseHtml = "";
                    licenseLink = [];
                    licenseText = [];
                    if(/BY/.exec(license)){
                        licenseHtml += "<span class='license-icon license-cc-by'></span>";
                        licenseLink.push("by");
                        licenseText.push(gettext("Attribution"));
                    }
                    if(/NC/.exec(license)){
                        licenseHtml += "<span class='license-icon license-cc-nc'></span>";
                        licenseLink.push("nc");
                        licenseText.push(gettext("NonCommercial"));
                    }
                    if(/SA/.exec(license)){
                        licenseHtml += "<span class='license-icon license-cc-sa'></span>";
                        licenseLink.push("sa");
                        licenseText.push(gettext("ShareAlike"));
                    }
                    if(/ND/.exec(license)){
                        licenseHtml += "<span class='license-icon license-cc-nd'></span>";
                        licenseLink.push("nd");
                        licenseText.push(gettext("NonDerivatives"));
                    }
                    licenseTooltip = interpolate(gettext("This work is licensed under a Creative Commons %(license_attributes)s %(version)s International License."), {
                            license_attributes: licenseText.join("-"),
                            version: licenseVersion
                        }, true);
                    return "<a rel='license' href='http://creativecommons.org/licenses/" +
                        licenseLink.join("-") + "/" + licenseVersion + "/' data-tooltip='" + licenseTooltip +
                        "' target='_blank' class='license'>" +
                        licenseHtml +
                        "<span class='license-text'>" +
                        gettext("Some rights reserved") +
                        "</span></a>";
                }
            },

        });

        return LicenseView;
    }
); // end define();
