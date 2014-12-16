define(["js/views/baseview", "underscore", "gettext", "js/models/license", "js/views/license-view"],
    function(BaseView, _, gettext, LicenseModel, LicenseView) {

        var LicenseSelector = BaseView.extend({
            events: {
                "click .license-button" : "onLicenseButtonClick",
            },

            initialize: function(options) {
                this.template = this.loadTemplate("license-selector");
                if (!this.model) {
                    this.model = new LicenseModel();
                }
                else if (!(this.model instanceof LicenseModel) && this.model.license) {
                    debugger;
                    this.model = new LicenseModel(this.model);
                }
                this.licenseView = new LicenseView({
                    model: this.model
                });
                
                // Rerender on model change
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                this.$el.html(this.template({
                    default_license: this.model.get('license'),
                    default_license_preview: this.licenseView.renderLicense()
                }));

                this.$el.addClass('license-selector');

                this.renderLicenseButtons();

                return this;
            },

            renderLicenseButtons: function() {
                var license, $cc;
                license = this.model.get('license');
                $cc = this.$el.find('.selected-cc-license-options');

                if (!license || license === "NONE" || license === "ARR") {
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

            onLicenseButtonClick: function(e) {
                var $button, $cc, buttonLicense, license, selected;

                $button = $(e.srcElement || e.target).closest('.license-button');
                $cc = this.$el.find('.license-cc-options');
                buttonLicense = $button.attr("data-license");

                if(buttonLicense === "ARR"){
                    license = buttonLicense;
                }
                else {
                    if($button.hasClass('selected') && (buttonLicense === "CC" || buttonLicense === "BY")){
                        // Abort, this attribute is not allowed to be unset through another click
                        return this;
                    }
                    $button.toggleClass("selected");

                    if (buttonLicense === "ND" && $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='SA']").removeClass("selected");
                    }
                    else if(buttonLicense === "SA" && $button.hasClass("selected")) {
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
