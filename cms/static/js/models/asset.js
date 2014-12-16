define(["backbone", "js/models/license", "backbone.associations"], function(Backbone, License) {
  /**
   * Simple model for an asset.
   */
  var Asset = Backbone.AssociatedModel.extend({
    defaults: {
      display_name: "",
      thumbnail: "",
      date_added: "",
      url: "",
      license: {},
      licenseable: false,
      external_url: "",
      portable_url: "",
      locked: false
    },

    relations: [{
        type: Backbone.One,
        key: 'license',
        relatedModel: License
    }],
  });
  return Asset;
});
