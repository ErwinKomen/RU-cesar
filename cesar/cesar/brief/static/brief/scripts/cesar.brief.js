var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      sil.pbrief.init_event_listeners();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

var sil = (function ($, sil) {
  "use strict";

  sil.pbrief = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "pbrief_err",
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
      textAreaAdjust: function (el) {
        var element = $(el)[0];

        if (element.scrollHeight > element.clientHeight) {
          element.style.height = (element.scrollHeight) + "px";
        }
      },
      errMsg: function (sMsg, ex) {
        var sHtml = "Error in [" + sMsg + "]<br>" + ex.message;
        $("#" + loc_divErr).html(sHtml);
      },
      errClear: function () {
        $("#" + loc_divErr).html("");
      }
    }

    // Public methods
    return {
      init_event_listeners: function () {
        try {
          // Automatically size textarea based on contents
          $("textarea").each(function (idx, el) {
            private_methods.textAreaAdjust(el);
          });
          // Make sure that adaptation happends upon keyboard input too
          $("textarea").on("keyup", function (evt) {
            var el = $(this);
            private_methods.textAreaAdjust(el);
          });

        } catch (ex) {
          private_methods.errMsg("init_event_listeners", ex);
        }
      },

      /**
       * do_button
       *   Show or hide edit mode
       *
       */
      do_button: function (elStart) {
        try {
          if ($(elStart).hasClass("view-mode")) {
            // Hide view mode
            $(".view-mode").addClass("hidden");
            // Show edit mode
            $(".edit-mode").removeClass("hidden");
          } else {
            // Show view mode
            $(".view-mode").removeClass("hidden");
            // Hide edit mode
            $(".edit-mode").addClass("hidden");
          }

        } catch (ex) {
          private_methods.errMsg("do_button", ex);
        }
      },

      /**
       * set_section
       *   Set the project/module/section
       *
       */
      set_section: function (elStart) {
        var data = null,
            elForm = "#send_location",
            target = "",
            arTarget = [],
            section = "",
            url = "";

        try {
          target = $(elStart).attr("data-target");
          arTarget = target.split("_");
          $("#module_no").val(arTarget[1].replace("m", ""));
          // Double check: are we opening or closing?
          if ($(elStart).hasClass("collapsed")) {
            // It is now opening up...
            section = arTarget[2].replace("s", "");
          } else {
            // It is closing down
            section = -1;
          }
          $("#section_no").val(section);
          url = $(elForm).attr("action");
          data = $(elForm).serializeArray();
          // Send the data
          $.post(url, data, function (response) {
            // First leg has been done
            if (response === undefined || response === null || !("status" in response)) {
              private_methods.errMsg("No status returned");
            } else {
              switch (response.status) {
                case "ok":
                  // No further action is needed
                  break;
                case "error":
                  if ("html" in response) {
                    private_methods.errMsg("error: " + response['html']);
                  }
                  break;
              }
            }
          });
        } catch (ex) {
          private_methods.errMsg("set_section", ex);
        }
      },

      /**
       * tabular_addrow
       *   Add one row into a tabular inline
       *
       */
      tabular_addrow: function (elStart, options) {
        // NOTE: see the definition of lAddTableRow above
        var oTdef = {},
            rowNew = null,
            elTable = null,
            select2_options = {},
            iNum = 0,     // Number of <tr class=form-row> (excluding the empty form)
            sId = "",
            bSelect2 = false,
            i;

        try {
          // Find out just where we are
          if (elStart === undefined || elStart === null || $(elStart).closest("div").length === 0)
            elStart = $(this);
          sId = $(elStart).closest("div[id]").attr("id");
          // Process options
          if (options !== undefined) {
            for (var prop in options) {
              switch (prop) {
                case "select2": bSelect2 = options[prop]; break;
              }
            }
          }
          // Get the definition
          oTdef = options;
          if (sId === oTdef.table || sId.indexOf(oTdef.table) >= 0) {
            // Go to the <tbody> and find the last form-row
            elTable = $(elStart).closest("tbody").children("tr.form-row.empty-form")

            if ("select2_options" in oTdef) {
              select2_options = oTdef.select2_options;
            }

            // Perform the cloneMore function to this <tr>
            rowNew = ru.basic.cloneMore(elTable, oTdef.prefix, oTdef.counter);
            // Call the event initialisation again
            if (oTdef.events !== null) {
              oTdef.events();
            }
            // Possible Select2 follow-up
            if (bSelect2) {
              // Remove previous .select2
              $(rowNew).find(".select2").remove();
              // Execute djangoSelect2()
              $(rowNew).find(".django-select2").djangoSelect2(select2_options);
            }
            // Any follow-up activity
            if ('follow' in oTdef && oTdef['follow'] !== null) {
              oTdef.follow(rowNew);
            }
          }
        } catch (ex) {
          private_methods.errMsg("tabular_addrow", ex);
        }
      },

      /**
       * delete_confirm
       *   Open the next <tr> to get delete confirmation (or not)
       *
       */
      delete_confirm: function (el, bNeedConfirm) {
        var elDiv = null;

        try {
          if (bNeedConfirm === undefined) { bNeedConfirm = true; }
          // Action depends on the need for confirmation
          if (bNeedConfirm) {
            // Find the [.delete-row] to be shown
            elDiv = $(el).closest("tr").find(".delete-confirm").first();
            if (elDiv.length === 0) {
              // Try goint to the next <tr>
              elDiv = $(el).closest("tr").next("tr.delete-confirm");
            }
            $(elDiv).removeClass("hidden");
          } else {

          }
        } catch (ex) {
          private_methods.errMsg("delete_confirm", ex);
        }
      },

      /**
       * tabular_deleterow
       *   Delete one row from a tabular inline
       *
       */
      tabular_deleterow: function (elStart) {
        var sId = "",
            elDiv = null,
            elRow = null,
            elPrev = null,
            elDel = null,   // The delete inbox
            sPrefix = "",
            elForms = "",
            counter = $(elStart).attr("counter"),
            deleteurl = "",
            data = [],
            frm = null,
            bCounter = false,
            bHideOnDelete = false,
            iForms = 0,
            prefix = "simplerel";

        try {
          // Get the prefix, if possible
          sPrefix = $(elStart).attr("extra");
          bCounter = (typeof counter !== typeof undefined && counter !== false && counter !== "");
          elForms = "#id_" + sPrefix + "-TOTAL_FORMS"
          // Find out just where we are
          elDiv = $(elStart).closest("div[id]")
          sId = $(elDiv).attr("id");
          // Find out how many forms there are right now
          iForms = $(elForms).val();
          frm = $(elStart).closest("form");

          // Get the deleteurl (if existing)
          deleteurl = $(elStart).attr("targeturl");
          // Only delete the current row
          elRow = $(elStart).closest("tr");
          // Do we need to hide or delete?
          if ($(elRow).hasClass("hide-on-delete")) {
            bHideOnDelete = true;
            $(elRow).addClass("hidden");
          } else {
            $(elRow).remove();
          }

          // Further action depends on whether the row just needs to be hidden
          if (bHideOnDelete) {
            // Row has been hidden: now find and set the DELETE checkbox
            elDel = $(elRow).find("input:checkbox[name$='DELETE']");
            if (elDel !== null) {
              $(elDel).prop("checked", true);
            }
          } else {
            // Decrease the amount of forms
            iForms -= 1;
            $(elForms).val(iForms);

            // Re-do the numbering of the forms that are shown
            $(elDiv).find(".form-row").not(".empty-form").each(function (idx, elThisRow) {
              var iCounter = 0, sRowId = "", arRowId = [];

              iCounter = idx + 1;
              // Adapt the ID attribute -- if it EXISTS
              sRowId = $(elThisRow).attr("id");
              if (sRowId !== undefined) {
                arRowId = sRowId.split("-");
                arRowId[1] = idx;
                sRowId = arRowId.join("-");
                $(elThisRow).attr("id", sRowId);
              }

              if (bCounter) {
                // Adjust the number in the FIRST <td>
                $(elThisRow).find("td").first().html(iCounter.toString());
              }

              // Adjust the numbering of the INPUT and SELECT in this row
              $(elThisRow).find("input, select").each(function (j, elInput) {
                // Adapt the name of this input
                var sName = $(elInput).attr("name");
                if (sName !== undefined) {
                  var arName = sName.split("-");
                  arName[1] = idx;
                  sName = arName.join("-");
                  $(elInput).attr("name", sName);
                  $(elInput).attr("id", "id_" + sName);
                }
              });
            });
          }

        } catch (ex) {
          private_methods.errMsg("tabular_deleterow", ex);
        }
      },

      /**
        * result_download
        *   Trigger creating and downloading a result CSV / XLSX / JSON
        *
        */
      post_download: function (elStart) {
        var ajaxurl = "",
            contentid = null,
            response = null,
            frm = null,
            el = null,
            sHtml = "",
            oBack = null,
            dtype = "",
            sMsg = "",
            method = "normal",
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");
          contentid = $(elStart).attr("contentid");

          // Gather the information
          frm = $(elStart).closest(".container-small").find("form");
          if (frm.length === 0) {
            frm = $(elStart).closest("td").find("form");
            if (frm.length === 0) {
              frm = $(elStart).closest(".body-content").find("form");
              if (frm.length === 0) {
                frm = $(elStart).closest(".container-large.body-content").find("form");
              }
            }
          }
          // Check what we have
          if (frm === null || frm.length === 0) {
            // Didn't find the form
            private_methods.errMsg("post_download: could not find form");
          } else {
            // Make sure we take only the first matching form
            frm = frm.first();
          }
          // Get the download type and put it in the <input>
          dtype = $(elStart).attr("downloadtype");
          $(frm).find("#downloadtype").val(dtype);

          switch (method) {
            case "erwin":
              data = frm.serialize();
              $.post(ajaxurl, data, function (response) {
                var iready = 1;
              });
              break;
            default:
              // Set the 'action; attribute in the form
              frm.attr("action", ajaxurl);
              // Make sure we do a POST
              frm.attr("method", "POST");

              // Do we have a contentid?
              if (contentid !== undefined && contentid !== null && contentid !== "") {
                // Process download data
                switch (dtype) {
                  default:
                    // TODO: add error message here
                    return;
                }
              } else {
                // Do a plain submit of the form
                oBack = frm.submit();
              }
              break;
          }

          // Check on what has been returned
          if (oBack !== null) {

          }
        } catch (ex) {
          private_methods.errMsg("post_download", ex);
        }
      },

      process_brief: function (elStart, divNotice, action) {
        var targeturl = "",
            frm = null,
            data = [],
            lst_todo = [],
            todo_id = "",
            todo_html = "",
            i = 0,
            datetime = "";

        try {
          // Get the targeturl
          targeturl = $(elStart).attr("targeturl");
          // Get the current form
          frm = $(elStart).closest("form");
          // FInd the data in this form
          data = frm.serializeArray();
          // Clear previous error message
          private_methods.errClear();
          // Process these data
          $.post(targeturl, data, function (response) {
            // First leg has been done
            if (response === undefined || response === null || !("status" in response)) {
              private_methods.errMsg("No status returned");
            } else {
              switch (response.status) {
                case "ok":
                  // FIgure out what the current date/time is
                  datetime = private_methods.get_currentdate();
                  $(divNotice).html("<i>(Saved at " + datetime + ")</i>");
                  // Get a possible list of todo stuff
                  if (response.typeaheads !== undefined) {
                    lst_todo = response.typeaheads;
                    for (i = 0; i < lst_todo.length; i++) {
                      todo_id = lst_todo[i].id;
                      todo_html = lst_todo[i].todo;
                      $("#" + todo_id).html(todo_html);
                    }
                  }
                  // Any action afterwards?
                  if (action !== undefined && action === "close") {
                    // Show view mode
                    $(".view-mode").removeClass("hidden");
                    // Hide edit mode
                    $(".edit-mode").addClass("hidden");
                  }

                  // Make sure the notice goes away after 5 seconds
                  window.setTimeout(function () {
                    $(divNotice).html("");
                  }, 2000);

                  break;
                case "error":
                  if ("html" in response) {
                    private_methods.errMsg("error: " + response['html']);
                  }
                  break;
              }
            }
          });
        } catch (ex) {
          private_methods.errMsg("process_pbrief", ex);
        }
      }

    };
  }($, sil.config));

  return sil;
}(jQuery, window.sil || {})); // window.sil: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

