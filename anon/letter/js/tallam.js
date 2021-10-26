var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      ru.tallam.init_event_listeners();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

// var $ = django.jQuery.noConflict();

var ru = (function ($, ru) {
  "use strict";

  ru.tallam = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "tallam_err",
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
      errMsg: function (sMsg, ex) {
        var sHtml = "Error in [" + sMsg + "]<br>" + ex.message;
        $("#" + loc_divErr).html(sHtml);
      }
    }

    // Public methods
    return {
      /**
       * init_event_listeners
       *    Initialize eent listeners for this module
       */
      init_event_listeners: function () {
        // Bind on the language choice changes radio buttons
        $(".language-choice input[type=radio]").bind('change', ru.tallam.lang_change);
        // Show the first language only
        $(".story").addClass("hidden");
        $(".story").first().removeClass("hidden");
      },

      /**
       *  view_switch
       *      Switch from one view to the other
       *
       */
      lang_change: function (ev) {
        var language = "";

        try {
          // Get the language
          language = ev.target.value;
          // Show that language and hide the others
          $(".story").addClass("hidden");
          $(".story[language='" + language + "']").removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("lang_change", ex);
        }
      },
    
      /**
       *  view_switch
       *      Switch from one view to the other
       *
       */
      view_switch: function (sOpen, sClose) {
        $("#" + sOpen).removeClass("hidden");
        $("#" + sClose).addClass("hidden");
        // Show/hide <li> elements
        $("li." + sOpen).removeClass("hidden");
        $("li." + sClose).addClass("hidden");
      }

    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

