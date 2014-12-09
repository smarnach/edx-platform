define(["jquery"], function($) {
    var license_to_img = function(license) {
        var imgUrl, licenseUrl, attr;
        if (license == "ARR") {
            return "<a target='_blank' href=''><img src='" + window.baseUrl + "images/arr.png' /></a>";
        }
        else if(license == "CC0") {
            licenseUrl = "http://i.creativecommons.org/l/zero/1.0/";
        }
        else {
            attr = license.toLowerCase().split("-");
            if (attr[0] != "cc") {
                return "No license.";
            }
            attr = attr.splice(1, attr.length - 1);

            licenseUrl = 'http://i.creativecommons.org/l/' + attr.join("-") + "/3.0/";
        }

        imgUrl = licenseUrl + "80x15.png";
        return "<a target='_blank' href='" + licenseUrl + "'><img src='" + imgUrl + "' /></a>";
    }

    return license_to_img;
});
