var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      ru.cesar.woord.init_event_listeners();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

var ru = (function ($, ru) {
  "use strict";

  ru.cesar.woord = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "woord_err",
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
       *   Set a listener to the progressbar
       *
       */
      init_event_listeners: function () {
        try {
          // Define what happens to the .slider elements
          $( ".slider" ).slider(
              { value:50,
                slide: function(event, ui) {
                  $(this).next().html(ui.value);
                }
              });

          // Set up the progressbar function
          $(function() {
            // Initially: nothing has happened
            $( "#progressbar" ).progressbar({value: 0 / 100.05});
          });


        } catch (ex) {
          private_methods.errMsg("init_event_listeners", ex);
        }
      },

      /**
       * volgende
       *   Show the next question
       *
       */
      volgende: function (elStart, username) {
        var result_string = "",
            result = null,
            percentage = 0.0,
            url = "",
            frm = null,
            csrf = "",
            data = null;

        try {
          $('.centerfield').each(function (index) {
            result = new Object();
            result.stimulus = $(this).find('.stimulus').html().trim();
            result.scale = $(this).find('.rightoption').html().trim();
            result.dontknow = $(this).find('.knowcheck').is(':checked');
            result.score = $(this).find('.slider').slider('option', 'value');
            result.questionid = $(this).find(".questionid").html().trim();

            result_string = result_string + JSON.stringify(result) + '\n';

          });

          // Put the results in the right name
          $("#results").val(result_string);

          // Get the form and the associated data
          frm = $(elStart).closest("form")
 
          // Submit it
          frm.submit();
  
        } catch (ex) {
          private_methods.errMsg("volgende", ex);
        }
      },

      /**
       * postman
       *   Post and process response
       *
       */
      postman: function(elStart) {
        var url = "",
            targetid = "",
            action = "",
            msg = "",
            data = null;

        try {

          // POST the response and find out what needs to be done
          url = $(elStart).attr("targeturl");
          targetid = $(elStart).attr("targetid");
          targetid = "#" + targetid.replace("#", "");
          action = $(elStart).attr("action");
          data = $("form").serializeArray();
          data.push({ name: "action", value: action });

          // Show we are starting
          $(targetid).html(loc_sWaiting);

          // Send the data
          $.post(url, data, function (response) {
            // First leg has been done
            if (response === undefined || response === null || !("status" in response)) {
              private_methods.errMsg("No status returned");
            } else {
              switch (response.status) {
                case "ok":
                  // Do we have a message to show?
                  if ("msg" in response) {
                    msg = response.msg;
                  } else {
                    msg = "";
                  }
                  $(targetid).html(msg);
                  break;
                case "error":
                  if ("html" in response) {
                    private_methods.errMsg("error: " + response['html']);
                  } else if ("msg" in response) {
                    private_methods.errMsg("error: " + response['msg']);
                  }
                  break;
              }
            }
          });

        } catch (ex) {
          private_methods.errMsg("postman", ex);
        }
      }

    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.sil: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

