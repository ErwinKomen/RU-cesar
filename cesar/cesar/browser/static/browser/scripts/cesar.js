(function ($) {
  $(function () {
    $(document).ready(function () {
      // Bind the keyup and change events
      $('#id_DCtype').bind('keyup', type_change);
      $('#id_DCtype').bind('change', type_change);
      $('#id_subtype >option').show();
      // Add 'copy' action to inlines
      tabinline_add_copy();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

var $ = django.jQuery.noConflict();

function type_change() {
  // Get the value of the selected [DCtype]
  var dctype_type = $('#id_DCtype').val();
  // Create the URL that is needed
  var url_prefix = $(".container[url_home]").attr("url_home");
  if (url_prefix === undefined) {
    url_prefix = $("#container").attr("url_home");
  }
  var sUrl = url_prefix + "subtype_choices/?dctype_type=" + dctype_type;
  // Make a request to get all subtype choices for this DCtype
  $.ajax({
    "type": "GET",
    "url": sUrl,
    "dataType": "json",
    "cache": false,
    "success": function (json) {
      $('#id_subtype >option').remove();
      for (var j = 0; j < json.length; j++) {
        $('#id_subtype').append($('<option></option>').val(json[j][0]).html(json[j][1]));
      }
    }
  })(jQuery);
}

/**
 * tabinline_add_copy
 *   Add a COPY button to all tabular inlines available
 */
function tabinline_add_copy() {
  $(".tabular .related-widget-wrapper").each(
    function (idx, obj) {
      // Find the first <a> child
      var chgNode = $(this).children("a").first();
      var sHref = $(chgNode).attr("href");
      if (sHref !== undefined) {
        // Remove from /change onwards
        var iChangePos = sHref.lastIndexOf("/change");
        if (iChangePos > 0) {
          sHref = sHref.substr(0, sHref.lastIndexOf("/change"));
          // Get the id
          var lastSlash = sHref.lastIndexOf("/");
          var sId = sHref.substr(lastSlash + 1);
          sHref = sHref.substr(0, lastSlash);
          // Get the model name
          lastSlash = sHref.lastIndexOf("/");
          var sModel = sHref.substr(lastSlash + 1);
          sHref = sHref.substr(0, lastSlash);
          // Find and adapt the history link's content to a current
          var sCurrent = $(".historylink").first().attr("href").replace("/history", "");
          // Create a new place to go to
          sHref = sHref.replace("collection", "copy") + "/?_popup=0&model=" + sModel + "&id=" + sId + "&current=" + sCurrent;
          var sAddNode = "<a class='copy-related' title='Make a copy' href='" + sHref + "'>copy</a>";
          // Append the new node
          $(this).append(sAddNode);
        }
      }
    });
}