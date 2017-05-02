﻿var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      ru.cesar.init_event_listeners();
      $('#id_subtype >option').show();
      // Add 'copy' action to inlines
      ru.cesar.tabinline_add_copy();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

// var $ = django.jQuery.noConflict();

var ru = (function ($, ru) {
  "use strict";

  ru.cesar = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        oSyncTimer = null;


    // Private methods specification
    var private_methods = {
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      }
    }

    // Public methods
    return {
      /**
       * init_event_listeners
       *    Initialize eent listeners for this module
       */
      init_event_listeners: function () {
        // Bind the keyup and change events
        // $('#id_DCtype').bind('keyup', ru.cesar.type_change);
        // $('#id_DCtype').bind('change', ru.cesar.type_change);
        // Bind the change event for text_list.html, 'part-name'
        $("#part-name").bind('change', ru.cesar.part_change);
        $("#part-name").change(ru.cesar.part_change);
      },
    
      type_change: function (el) {
        // Figure out how we are called
        if (el.type === "change" || el.type === "keyup") {
          // Need to get the element proper
          el = this;
        }
        // Get the value of the selected [DCtype]
        // var dctype_type = $('#id_DCtype').val();
        var dctype_type = $(el).val();
        var sIdSub = $(el).attr("id").replace("DCtype", "subtype");
        // Create the URL that is needed
        var url_prefix = $(".container[url_home]").attr("url_home");
        if (url_prefix === undefined) {
          url_prefix = $("#container").attr("url_home");
        }
        var sUrl = url_prefix + "subtype_choices/?dctype_type=" + dctype_type;
        // Define the options
        var ajaxoptions = {
          type: "GET",
          url: sUrl,
          dataType: "json",
          async: false,
          success: function (json) {
            $('#' + sIdSub + ' >option').remove();
            for (var j = 0; j < json.length; j++) {
              $('#' + sIdSub).append($('<option></option>').val(json[j][0]).html(json[j][1]));
            }
            // Set the selected value correctly
            $("#" + sIdSub).val(parseInt(dctype_type, 10));
          }
        };
        // Execute the ajax request SYNCHRONOUSLY
        $.ajax(ajaxoptions);
        // Do something else to provide a break point
        var k = 0;
      },


      /**
       * part_change: act on a change in selected 'part' in text_list.html
       */
      part_change : function() {
        // Get the name of the part that has been chosen
        var sPartName = $("#part-name option:selected").html();
        // Show this name
        $("#corpus_selected").html("<b>" + sPartName + "</b>");
      },


      /**
       * tabinline_add_copy
       *   Add a COPY button to all tabular inlines available
       */
      tabinline_add_copy: function () {
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
      },

      /**
       *  sync_start
       *      Start synchronisation
       *
       */
      sync_start : function(sSyncType) {
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
        ru.cesar.oSyncTimer = window.setTimeout(function () { ru.cesar.sync_progress(sSyncType, oJson); }, 3000);

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
          "success": function (json) { ru.cesar.sync_stop(sSyncType, json); }
        })(jQuery);
      },

      /**
       *  sync_progress
       *      Return the progress of synchronization
       *
       */
      sync_progress: function (sSyncType) {
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
            ru.cesar.sync_handle(sSyncType, json);
          }
        })(jQuery);
      },

      /**
       *  sync_handle
       *      Process synchronisation
       *
       */
      sync_handle: function (sSyncType, json) {
        var sStatus = "";

        // Validate
        if (json === undefined) {
          sStatus = $("#sync_details_" + sSyncType).html();
          $("#sync_details_" + sSyncType).html(sStatus + "(undefined status)");
          return;
        }
        // Action depends on the status in [json]
        switch (json.status) {
          case 'error':
            // Show we are ready
            $("#sync_progress_" + sSyncType).html("Error synchronizing: " + sSyncType);
            $("#sync_details_" + sSyncType).html(ru.cesar.sync_details(json));
            // Stop the progress calling
            window.clearInterval(ru.cesar.oSyncTimer);
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
            ru.cesar.oSyncTimer = window.setTimeout(function (json) { ru.cesar.sync_progress(sSyncType); }, 1000);
            break;
        }
      },

      /**
       *  sync_stop
       *      Finalize synchronisation
       *
       */
      sync_stop: function (sSyncType, json) {
        var lHtml = [];

        // Stop the progress calling
        window.clearInterval(ru.cesar.oSyncTimer);
        // Show we are ready
        $("#sync_progress_" + sSyncType).html("Finished synchronizing: " + sSyncType + "<br>" + JSON.stringify(json, null, 2));

      },

      /**
       *  sync_details
       *      Return a string with synchronisation details
       *
       */
      sync_details: function (json) {
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
      },

      /**
       *  part_detail_toggle
       *      Toggle part detail
       *
       */
      part_detail_toggle: function (iPk) {
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

    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

