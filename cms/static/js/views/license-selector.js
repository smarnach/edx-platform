define(["js/views/baseview", "underscore", "gettext", "js/models/license"],
    function(BaseView, _, gettext, LicenseModel) {

        var LicenseSelector = BaseView.extend({
            events: {
                "click .license-button" : "onLicenseButtonClick",
            },
            options: {
                imgSize : false,
            },

            initialize: function(options) {
                this.template = this.loadTemplate("license-selector");
                if (!this.model) {
                    this.model = new LicenseModel();
                }
                else if (!(this.model instanceof LicenseModel)) {
                    this.model = new LicenseModel(this.model)
                }
                
                // Rerender on model change
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                this.$el.html(this.template({
                    default_license: this.model.get('license'),
                    default_license_preview: this.renderLicense()
                }));

                this.$el.addClass('license-selector');

                this.renderLicenseButtons();

                return this;
            },

            renderLicenseButtons: function() {
                var license, $cc;
                license = this.model.get('license');
                $cc = this.$el.find('.selected-cc-license-options');

                if (!license || license == "NONE" || license == "ARR") {
                    this.$el.find('.license-button[data-license="ARR"]').addClass('selected');
                    this.$el.find('.license-button[data-license="CC"]').removeClass('selected');
                    $cc.hide();
                }
                else {
                    var attr = license.split("-");
                    this.$el.find('.license-button').removeClass('selected');
                    for(i in attr) {
                        this.$el.find('.license-button[data-license="' + attr[i] + '"]').addClass('selected');
                    }
                    $cc.show();
                }

                return this;
            },

            renderLicense: function() {
                var license, licenseHtml, licenseText, licenseLink, licenseTooltip;
                license = (this.model.get('license') || "none").toLowerCase();

                if(license == "none" || license == "arr"){
                    // All rights reserved
                    licenseText = gettext("All rights reserved")
                    return "<span class='license-icon license-arr'></span><span class='license-text'>" + licenseText + "</span>";
                }
                else if(license == "cc0"){
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
                    if(/by/.exec(license)){
                        licenseHtml += "<span class='license-icon license-cc-by'></span>";
                        licenseLink.push("by");
                        licenseText.push(gettext("Attribution"));
                    }
                    if(/nc/.exec(license)){
                        licenseHtml += "<span class='license-icon license-cc-nc'></span>";
                        licenseLink.push("nc");
                        licenseText.push(gettext("NonCommercial"));
                    }
                    if(/sa/.exec(license)){
                        licenseHtml += "<span class='license-icon license-cc-sa'></span>";
                        licenseLink.push("sa");
                        licenseText.push(gettext("ShareAlike"));
                    }
                    if(/nd/.exec(license)){
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

            onLicenseButtonClick: function(e) {
                var $button, $cc, buttonLicense, license, selected;

                $button = $(e.srcElement || e.target).closest('.license-button');
                $cc = this.$el.find('.license-cc-options');
                buttonLicense = $button.attr("data-license");

                if(buttonLicense == "ARR"){
                    license = buttonLicense;
                }
                else {
                    if($button.hasClass('selected') && (buttonLicense == "CC" || buttonLicense == "BY")){
                        // Abort, this attribute is not allowed to be unset through another click
                        return this;
                    }
                    $button.toggleClass("selected");

                    if (buttonLicense == "ND" && $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='SA']").removeClass("selected");
                    }
                    else if(buttonLicense == "SA" && $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='ND']").removeClass("selected");
                    }

                    license = "CC";
                    $cc.children(".license-button[data-license='BY']").addClass("selected");
                    selected = $cc.children(".selected");
                    selected.each( function() {
                        license = license + "-" + $(this).attr("data-license");
                    });
                }

                this.model.set('license', license);

                return this;
            },

        });

        return LicenseSelector;
    }
); // end define();
