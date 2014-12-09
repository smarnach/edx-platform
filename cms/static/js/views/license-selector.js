define(["js/views/baseview", "underscore", "gettext", "js/models/license"],
    function(BaseView, _, gettext, LicenseModel) {

        var LicenseSelector = BaseView.extend({
            events: {
                "click .license-button" : "onLicenseButtonClick",
            },
            options: {
                buttonSize : false,
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
            },

            setLicense: function(newLicense) {
                this.model.set({'license': newLicense})
                this.setLicenseButtons();
            },

            render: function() {
                this.$el.html(this.template({
                    default_license: this.model.get('license'),
                    default_license_img: this.img()
                }));

                this.$el.addClass('license-selector');

                if (this.options.buttonSize) {
                    this.$el.find('.license-button').addClass('size-' + this.options.buttonSize);
                }

                this.$el.find('.license').val(JSON.stringify(this.model.toJSON()));
                this.$el.find('.selected-license').html(this.img());
                this.setLicenseButtons();

                return this;
            },

            setLicenseButtons: function() {
                var license = this.model.get('license');
                this.$el.find('.license-cc .license-button').removeClass('selected');

                if (!license || license == "NONE") {
                    this.$el.find('.license-button').removeClass('selected');
                    this.$el.find('.license-allornothing').removeClass('selected');
                    this.$el.find('.license-cc').removeClass('selected');
                }
                else if (license == "ARR") {
                    this.$el.find('.license-button[data-license="ARR"]').addClass('selected');
                    this.$el.find('.license-button[data-license="CC0"]').removeClass('selected');
                }
                else if (license == "CC0") {
                    this.$el.find('.license-button[data-license="CC0"]').addClass('selected');
                    this.$el.find('.license-button[data-license="ARR"]').removeClass('selected');
                }
                else {
                    var attr = license.split("-");

                    if (attr.length > 1 && attr[0] == "CC" && attr[1] == "BY") {
                        for(i in attr) {
                            this.$el.find('.license-button[data-license="' + attr[i] + '"]').addClass('selected');
                        }
                    }
                }

                // Toggle between custom license and allornothing
                if (license == "ARR" || license == "CC0") {
                    this.$el.find('.license-allornothing').addClass('selected');
                    this.$el.find('.license-cc').removeClass('selected');
                }
                else if (license != "NONE") {
                    this.$el.find('.license-cc').addClass('selected');
                    this.$el.find('.license-allornothing').removeClass('selected').children().removeClass("selected");
                }

                return this;
            },

            img: function() {
                var license, imgSize, imgUrl;
                license = this.model.get('license').toLowerCase();

                if (this.options.imgSize == "big") {
                    imgSize = "88x31";
                }
                else {
                    imgSize = "80x15";
                }
                
                imgUrl = "";
                switch(license) {
                    case "arr":
                        imgUrl = window.baseUrl + 'images/arr/';
                    break;
                    case "cc0":
                        imgUrl = "http://i.creativecommons.org/l/zero/1.0/";
                    break;
                    case "none":
                        return "None";
                    break;
                    
                    // Creative commons license
                    default:
                        imgUrl = 'http://i.creativecommons.org/l/' + license.substring(3, license.length) + "/3.0/";
                }

                return "<img src='" + imgUrl + imgSize + ".png' />";
            },

            onLicenseButtonClick: function(e) {
                var $button, $allornothing, $cc, license, selected;

                $button = $(e.srcElement || e.target).closest('.license-button');
                $allornothing = this.$el.find('.license-allornothing');
                $cc = this.$el.find('.license-cc');

                if($cc.has($button).length == 0) {
                    license = $button.attr("data-license");
                }
                else {
                    $button.toggleClass("selected");

                    if ($button.attr("data-license") == "ND" && $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='SA']").removeClass("selected");
                    }
                    else if($button.attr("data-license") == "SA"&& $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='ND']").removeClass("selected");
                    }

                    if ($button.attr("data-license") == "BY" && !$button.hasClass("selected")) {
                        license = "CC0";
                    }
                    else {
                        license = "CC";
                        $cc.children(".license-button[data-license='BY']").addClass("selected");
                        selected = $cc.children(".selected");
                        selected.each( function() {
                            license = license + "-" + $(this).attr("data-license");
                        });
                    }
                }

                this.model.set('license', license);

                return this;
            },

        });

        return LicenseSelector;
    }
); // end define();
