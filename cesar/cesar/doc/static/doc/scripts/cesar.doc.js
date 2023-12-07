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
      // Try load scatter plot chart
      //ru.cesar.doc.init_scatterplot();
    });
  });
})(django.jQuery);


// based on the type, action will be loaded

var ru = (function ($, ru) {
  "use strict";

  ru.cesar.doc = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_concrete = {},      // Score per word-id
        loc_loctime = {},       // Score per (location/time) multi-word expression
        loc_divErr = "doc_err",
        loc_sWaiting = " <span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>",
        loc_month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        loc_COLORS = ['#4dc9f6','#f67019','#f53794','#537bc4', '#acc236', '#166a8f', '#00a950', '#58595b', '#8549ba'],
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

      color: function (index) {
        return loc_COLORS[index % loc_COLORS.length];
      },

      numberWithCommas: function (x) {
        var parts = x.toString().split(".");
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        return parts.join(".");
      },

      log_axis: function (value, index, values) {
        if (value == 1e+1 || value == 2e+1 || value == 5e+1 ||
          value == 1e+2 || value == 2e+2 || value == 5e+2 ||
          value == 1e+3 || value == 2e+3 || value == 5e+3 ||
          value == 1e+4 || value == 2e+4 || value == 5e+4 ||
          value == 1e+5 || value == 2e+5 || value == 5e+5 ||
          value == 1e+6 || value == 2e+6 || value == 5e+6 ||
          value == 1e+7 || value == 2e+7 || value == 5e+7 ||
          value == 1e+8 || value == 2e+8 || value == 5e+8 ||
          value == 1e+9 || value == 2e+9 || value == 5e+9 ||
          value == 1e+10 || value == 2e+10 || value == 5e+10 ||
          value == 1e+11 || value == 2e+11 || value == 5e+11 ||
          value == 1e+12) {
          return private_methods.numberWithCommas(value);
        }
      },

      log_ticks: function (chartObj) {
        chartObj.ticks = [];
        chartObj.ticks.push(1);
        chartObj.ticks.push(10);
        chartObj.ticks.push(50);
        chartObj.ticks.push(100);
        chartObj.ticks.push(200);
        chartObj.ticks.push(400);
        chartObj.ticks.push(800);
        chartObj.ticks.push(1000);
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
                sLocTime = "",
                word_id = 0;

            if ($(this).text() !== $(this).data("currentText")) {
              // Signal that the SAVE button must display
              $(this).trigger("change");
              // Get the new float value
              fNew = parseFloat(e.target.textContent.trim().replace(/,/, "."));
              // Find out what situation we are in
              if ($(e.target).hasClass("loctime-score")) {
                // This is a location/time score: edit its score
                sLocTime = $(e.target).closest(".loctime-add").find(".loctime-mwe").text().trim();
                loc_loctime[sLocTime] = fNew;
              } else {
                // Get the word id
                word_id = parseInt(e.target.attributes['wordid'].value, 10);
                // Add to dictionary
                loc_concrete[word_id] = fNew;
              }
            }
          });
          $("[contenteditable=true]").on('change', function (e) {
            $("#concrete_process").removeClass("hidden");
            $(".scrolltop-container").addClass("scrolltop-save");
            $(".scrolltop-container a").removeClass("hidden");
            $(".scrolltop-container .arrow").addClass("hidden");
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
       * make_scatterplot
       *   Create scatter plot
       *
       */
      make_scatterplot: function (elStart) {
        var frm = null,
            config = null,
            data = null,
            chart = null,
            targeturl = "",
            idx = 0,
            plotdata = null,
            dataset = null,
            elWait = "#scatter_plot_wait",
            elView = "#scatter_plot_view",
            targetid = "#scatter_plot";

        try {
          // Indicate we are waiting
          $(elWait).removeClass("hidden");
          $(targetid).removeClass("hidden");
          // Get to the form 
          frm = $(targetid).find("form").first();
          data = frm.serializeArray();
          // Get more specifics
          targeturl = $(frm).attr("action");
          // Go and call
          $.post(targeturl, data, function (response) {
            // Action depends on the response
            if (response === undefined || response === null || typeof (response) === "string" || !("status" in response)) {
              private_methods.errMsg("No status returned");
            } else {
              $(elWait).addClass("hidden");
              switch (response.status) {
                case "ready":
                case "ok":
                  // Get the data and the options
                  config = response.config;
                  // Set and check the colors
                  for (idx = 0; idx < config.data.datasets.length; idx++) {
                    config.data.datasets[idx].backgroundColor = private_methods.color(idx);
                  }
                  // Set the yAxis callback function
                  config.options.scales.xAxes[0].ticks.callback = private_methods.log_axis;
                  // config.options.scales.xAxes[0].afterBuildTicks = private_methods.log_ticks;

                  // Create the chart - this uses chartjs
                  chart = new Chart($(elView), config);
                  chart.update();
                  break;
                case "error":
                  // Show the error
                  if ('msg' in response) {
                    $(targetid).html(response.msg);
                  } else {
                    $(targetid).html("An error has occurred (cesar.doc.js: make_scatterplot)");
                  }
                  break;
              }
            }
          });

        } catch (ex) {
          private_methods.errMsg("make_scatterplot", ex);
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
            concretedata = {},
            frm = null,
            data = null;

        try {
          // Set the result classes to indicate we are waiting
          $(".doc-result").html(loc_sWaiting);

          // Find the target table
          divTable = $(elStart).closest(".container-small").find("table.func-view").first();

          // Set the concretedata input to the current list
          concretedata = {scores: loc_concrete, loctime: loc_loctime};
          // WAS: $("#concretedata").val(JSON.stringify(loc_concrete));
          $("#concretedata").val(JSON.stringify(concretedata));

          // Reset the changes
          loc_concrete = {};
          loc_loctime = {};

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
       * doc_level
       *   Change the document view level
       *
       */
      doc_level: function (elThis) {
        var sLevel = "",
            elTable = null;

        try {
          // Get the overall table
          elTable = $(elThis).closest(".container-small").find("table").first();
          // Get the currently selected level
          sLevel = $(elThis).val();
          switch (sLevel) {
            case "all":
              // Remove 'hidden' from particular classes
              $(elTable).find(".doc-para, .doc-sent, .docword").removeClass("hidden");
              break;
            case "sent":
              // Hide words
              $(elTable).find(".doc-para, .doc-sent").removeClass("hidden");
              $(elTable).find(".docword").addClass("hidden");
              break;
            case "para":
              // Hide words, sent
              $(elTable).find(".doc-para").removeClass("hidden");
              $(elTable).find(".docword, .doc-sent").addClass("hidden");
              break;
            case "text":
              // Hide words, sent, para
              $(elTable).find(".docword, .doc-para, .doc-sent").addClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("doc_level", ex);
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

      /**
       * loctime_allowdrop
       *   Open this as a dropping zone
       *
       */
      loctime_allowdrop: function (ev) {
        try {
          ev.preventDefault();
        } catch (ex) {
          private_methods.errMsg("loctime_allowdrop", ex);
        }
      },

      /**
       * loctime_filter
       *   Filter table
       *
       */
      loctime_filter: function (elStart) {
        var sQuery = "",
            iCount = 0,
            elItems = null,
            elTable = null;

        try {
          // Get the table
          elTable = $(elStart).closest(".loctime-list").first();
          // Get the .loctime-items 
          elItems = $(elTable).find(".loctime-items").first();
          // Get the search string
          sQuery = $(elStart).val();
          if (sQuery !== undefined && sQuery !== "") {
            sQuery = sQuery.toLowerCase();
            if (sQuery !== "") {
              sQuery = sQuery.trim();
            }
            // iCount = 0;
            // Walk all rows of the table
            $(elTable).find("tr").each(function (idx, el) {
              var sItem = "",
                  pos = -1;

              // Match with contents of this row
              sItem = $(el).find("td").first().text().trim().toLowerCase();
              pos = sItem.indexOf(sQuery);
              if (pos < 0) {
                // no match
                $(el).addClass("hidden");
              } else {
                $(el).removeClass("hidden");
                // iCount += 1;
              }
            });
          } else {
            $(elTable).find("tr").removeClass("hidden");
          }
          // Show the total amount of rows
          iCount = $(elTable).find("tr").not(".hidden").length;
          $(elItems).html(iCount + " found");
        } catch (ex) {
          private_methods.errMsg("loctime_filter", ex);
        }
      },

      /**
       * loctime_drop
       *   Allow dropping
       *
       */
      loctime_drop: function (ev) {
        var elTd = null,
            idx = 0,
            selection = null,
            selText = "";

        try {
          // Disable other stuff
          ev.preventDefault();

          // Get the text that has been transferred
          // data = ev.dataTransfer.getData("text");

          // Get the selected text
          selection = window.getSelection();
          selText = selection.toString().trim();
          // Show the text
          elTd = $(ev.target).closest("td");
          $(elTd).find(".loctime-mwe").text(selText);
          $(elTd).find(".loctime-add").removeClass("hidden");
          // Add the combination to the table
          if (!(selText in loc_loctime)) {
            // Initialize it to zero -- the user must be able to change it
            loc_loctime[selText] = 0.0;
          }
          // Note: the SAVE button is only showed after this number has been edited
        } catch (ex) {
          private_methods.errMsg("loctime_drop", ex);
        }
      },

      /**
       * score_remove
       *   Remove this line of score
       *
       */
      score_remove: function (elStart) {
        var elTr = null,
            elWord = null,
            word_id = "";

        try {
          // Find the current <tr>
          elTr = $(elStart).closest("tr");
          // Get the word
          elWord = $(elTr).find("[wordid]").first();
          if ($(elWord).length > 0) {
            // Get the word id
            word_id = parseInt($(elWord)[0].attributes['wordid'].value, 10);
            // Add a -1 to the dictionary to indicate its removal
            loc_concrete[word_id] = -1;
            // Remove this row visually
            $(elTr).remove();
            // Make sure the save button shows
            $("#concrete_process").removeClass("hidden");
            $(".scrolltop-container").addClass("scrolltop-save");
            $(".scrolltop-container a").removeClass("hidden");
            $(".scrolltop-container .arrow").addClass("hidden");

          }
        } catch (ex) {
          private_methods.errMsg("score_remove", ex);
        }
      },

    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.sil: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

