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
var oSyncTimer = null;

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

function sync_start(sSyncType) {
  var oJson = {},
      oData = {},
      i,
      sParam = "",
      arKV = [],
      arParam = [],
      sUrl = "";

  // Indicate that we are starting
  $("#sync_progress_" + sSyncType).html("Repair is starting: " + sSyncType);
  // Start looking only after some time
  oJson = { 'status': 'started' };
  oSyncTimer = window.setTimeout(function () { sync_progress(sSyncType, oJson); }, 3000);

  // Make sure that at the end: we stop
  oData = { 'type': sSyncType };
  // More data may be needed for particular types
  switch (sSyncType) {
    case "texts":
      // Retrieve the parameters from the <form> settings
      sParam = $("#sync_form_" + sSyncType).serialize();
      arParam = sParam.split("&");
      for (i = 0; i < arParam.length; i++) {
        arKV = arParam[i].split("=");
        // Store the parameters into a JSON object
        oData[arKV[0]] = arKV[1];
      }
      break;
  }

  // Define the URL
  sUrl = $("#sync_start_" + sSyncType).attr('sync-start');
  $.ajax({
    "url": sUrl,
    "dataType": "json",
    "data": oData,      // This sends the parameters in the data object
    "cache": false,
    "success": function () { sync_stop(sSyncType); }
  })(jQuery);
}

function sync_progress(sSyncType) {
  var oData = {},
      sUrl = "";

  oData = { 'type': sSyncType };
  sUrl = $("#sync_start_" + sSyncType).attr('sync-progress');
  $.ajax({
    "url": sUrl,
    "dataType": "json",
    "data": oData,
    "cache": false,
    "success": function (json) {
      sync_handle(sSyncType, json);
    }
  })(jQuery);
}

function sync_handle(sSyncType, json) {
  // Action depends on the status in [json]
  switch (json.status) {
    case 'error':
      // Show we are ready
      $("#sync_progress_" + sSyncType).html("Error synchronizing: " + sSyncType);
      $("#sync_details_" + sSyncType).html(sync_details(json));
      // Stop the progress calling
      window.clearInterval(oSyncTimer);
      // Leave the routine, and don't return anymore
      return;
    case "done":
      // Finish nicely
      sync_stop(sSyncType, json);
      return;
    default:
      // Default action is to show the status
      $("#sync_progress_" + sSyncType).html(json.status);
      $("#sync_details_" + sSyncType).html(sync_details(json));
      oSyncTimer = window.setTimeout(function (json) { sync_progress(sSyncType); }, 1000);
      break;
  }
}

function sync_stop(sSyncType, json) {
  var lHtml = [];

  // Stop the progress calling
  window.clearInterval(oSyncTimer);
  // Show we are ready
  $("#sync_progress_" + sSyncType).html("Finished synchronizing: " + sSyncType);

}

function sync_details(json) {
  var lHtml = [],
      oCount = {};

  // Validate
  if (json === undefined || !json.hasOwnProperty("count"))
    return "";
  // Get the counts
  oCount = JSON.parse(json['count']);
  // Create a reply
  lHtml.push("<div><table><thead><tr><th></th><th></th></tr></thead><tbody>");
  for (var property in oCount) {
    if (oCount.hasOwnProperty(property)) {
      lHtml.push("<tr><td>" + property + "</td><td>" + oCount[property] + "</td></tr>");
    }
  }
  lHtml.push("</tbody></table></div>");
  // Return as string
  return lHtml.join("\n");
}

function part_detail_toggle(iPk) {
  var sId = "";

  // validate
  if (iPk === undefined) return;
  // Get the name of the tag
  sId = "#part_details_" + iPk.toString();
  // Check if it is visible or not
  if ($(sId).hasClass("hidden")) {
    // Remove it
    $(sId).removeClass("hidden");
  } else {
    // Add it
    $(sId).addClass("hidden");
  }
}
