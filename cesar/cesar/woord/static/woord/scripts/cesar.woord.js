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

var ru = (function ($, ru) {
  "use strict";

  ru.cesar.woord = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "woord_err",
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
            data = null;

        try {
          $('.centerfield').each(function (index) {
            result = new Object();
            result.stimulus = $(this).find('.stimulus').html().trim();
            result.scale = $(this).find('.rightoption').html().trim();
            result.dontknow = $(this).find('.knowcheck').is(':checked');
            result.score = $(this).find('.slider').slider('option', 'value');

            result_string = result_string + JSON.stringify(result) + '\n';

          });

          // POST the response and find out what needs to be done
          url = $(elStart).attr("targeturl");
          data = { 'user': username, 'results': result_string };
          // Send the data
          $.post(url, data, function (response) {
            // First leg has been done
            if (response === undefined || response === null || !("status" in response)) {
              private_methods.errMsg("No status returned");
            } else {
              switch (response.status) {
                case "ok":
                  // Fetch the percentage from the results
                  percentage = response.percentage;
                  // Set the progressbar correctly
                  $("#progressbar").progressbar({ value: percentage });
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
          private_methods.errMsg("volgende", ex);
        }
      },

      /**
       * show_slider
       *   Show the slider
       *
       */


    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.sil: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

