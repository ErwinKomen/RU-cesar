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

      process_brief: function (elStart, divNotice) {
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

