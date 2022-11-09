var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      ru.cesar.doc.init_event_listeners();
    });
  });
})(django.jQuery);


// based on the type, action will be loaded

var ru = (function ($, ru) {
  "use strict";

  ru.cesar.doc = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_concrete = {},
        loc_divErr = "doc_err",
        loc_sWaiting = " <span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>",
        loc_month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        oSyncTimer = null;


    // Private methods specification
    var private_methods = {
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      },

      /**
       * get_currentdate -
       *    Get the current date in a human readable form
       */
      get_currentdate: function () {
        var currentdate = new Date(),
            month = "",
            hour = "",
            minute = "",
            second = "",
            combi = "";

        month = loc_month[currentdate.getMonth()];
        hour = currentdate.getHours().toString().padStart(2, "0");
        minute = currentdate.getMinutes().toString().padStart(2, "0");
        second = currentdate.getSeconds().toString().padStart(2, "0");
        combi = currentdate.getDay() + "/" + month + "/" + currentdate.getFullYear() +
                    " @ " + hour + ":" + minute + ":" + second;
        return combi;
      },

      copyToClipboard: function (elem) {
        // create hidden text element, if it doesn't already exist
        var targetId = "_hiddenCopyText_";
        var datatarget = "";
        var elConfirm = "";
        var isInput = "";
        var origSelectionStart, origSelectionEnd;

        try {
          // Get to the right element
          if (elem.tagName === "A") {
            // Do we have a data target?
            datatarget = $(elem).attr("data-target");
            if (datatarget === undefined || datatarget === "") {
              elem = $(elem).closest("div").find("textarea").first().get(0);
            } else {
              elem = $("#" + datatarget).first().get(0);
            }
          }
          isInput = elem.tagName === "INPUT" || elem.tagName === "TEXTAREA";
          if (isInput) {
            // can just use the original source element for the selection and copy
            target = elem;
            origSelectionStart = elem.selectionStart;
            origSelectionEnd = elem.selectionEnd;
          } else {
            // must use a temporary form element for the selection and copy
            target = document.getElementById(targetId);
            if (!target) {
              var target = document.createElement("textarea");
              target.style.position = "absolute";
              target.style.left = "-9999px";
              target.style.top = "0";
              target.id = targetId;
              document.body.appendChild(target);
            }
            // target.textContent = elem.textContent;
            $(target).html($(elem).html());
            // Testing
          }
          // select the content
          var currentFocus = document.activeElement;
          target.focus();
          target.setSelectionRange(0, target.value.length);

          // copy the selection
          var succeed;
          try {
            succeed = document.execCommand("copy");
            console.log("Copied: " + target.value);
            elConfirm = $(elem).closest("div").find(".clipboard-confirm").first();
            $(elConfirm).html("Copied!");
            setTimeout(function () {
              $(elConfirm).fadeOut().empty();
            }, 4000);
          } catch (e) {
            succeed = false;
            console.log("Could not copy");
          }
          // restore original focus
          if (currentFocus && typeof currentFocus.focus === "function") {
            currentFocus.focus();
          }

          if (isInput) {
            // restore prior selection
            elem.setSelectionRange(origSelectionStart, origSelectionEnd);
          } else {
            // clear temporary content
            target.textContent = "";
          }

          return succeed;
        } catch (ex) {
          private_methods.errMsg("copyToClipboard", ex);
          return "";
        }

      },

      /**
       * errMsg -
       *    Give an error message at loc_divErr
       */
      errMsg: function (sMsg, ex) {
        var msg = "",
            sHtml = "";

        if (ex !== undefined) {
          msg = ex.message;
        }
        sHtml = "Error in [" + sMsg + "]<br>" + msg;
        $("#" + loc_divErr).html(sHtml);
      },

      /**
       * errClear -
       *    Reset loc_divErr
       */
      errClear: function () {
        $("#" + loc_divErr).html("");
      }
    }

    // Public methods
    return {
      /**
       * init_event_listeners
       *
       */
      init_event_listeners: function () {
        try {

          // CLear errors
          private_methods.errClear();

          $("[contenteditable=true]").on("focus", function (e) { $(this).data("currentText", $(this).text()); });

          $("[contenteditable=true]").on('blur', function (e) {
            var fNew = 0.0,
                word_id = 0;

            if ($(this).text() !== $(this).data("currentText")) {
              // Signal that the SAVE button must display
              $(this).trigger("change");
              // Get the new float value
              fNew = parseFloat(e.target.textContent.trim().replace(/,/, "."));
              // Get the word id
              word_id = parseInt(e.target.attributes['wordid'].value, 10);
              // Add to dictionary
              loc_concrete[word_id] = fNew;
            }
          });
          $("[contenteditable=true]").on('change', function (e) {
            $("#concrete_process").removeClass("hidden");
          });

          // clipboard copying
          $(".clipboard-copy").unbind("click").on("click", function (evt) {
            private_methods.copyToClipboard(this);
          });

        } catch (ex) {
          private_methods.errMsg("init_event_listeners", ex);
        }
      },

      /**
       * concrete_changes
       *   Process changes in concreteness
       *
       */
      concrete_changes: function (elStart) {
        var ajaxurl = "",
            divTarget = "",
            divTable = "",
            elConcreteData = "",
            posturl = "",
            geturl = "",
            frm = null,
            data = null;

        try {
          // Set the result classes to indicate we are waiting
          $(".doc-result").html(loc_sWaiting);

          // Find the target table
          divTable = $(elStart).closest(".container-small").find("table.func-view").first();

          // Set the concretedata input to the current list
          $("#concretedata").val(JSON.stringify(loc_concrete));

          // Reset the changes
          loc_concrete = {};

          // Get the form and the associated data
          frm = $(elStart).closest("form");
          posturl = $(frm).attr("action");
          geturl = $(elStart).attr("targeturl");
          data = frm.serializeArray();
          $.post(posturl, data, function (e) {
            // The data has been processed, now re-load
            window.location = geturl;
          });

        } catch (ex) {
          private_methods.errMsg("concrete_changes", ex);
        }
      },

      /**
       * hnym_select
       *   Process change in homonym selection
       *
       */
      hnym_select: function (elStart) {
        var elTr = null,
            hnym_id = "",
            score = "",
            elEditable = null;

        try {
          elTr = $(elStart).closest("tr.docword");
          elEditable = $(elTr).find("[contenteditable=true]").first();
          // Get the value of the selected one
          hnym_id = $(elStart).val();
          score = $(elStart).find("option[value='" + hnym_id + "']").attr("score");
          $(elEditable).html(score);
          // Trigger processing the numerical change
          $(elEditable).trigger("blur");
        } catch (ex) {
          private_methods.errMsg("hnym_select", ex);
        }
      },

    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.sil: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

