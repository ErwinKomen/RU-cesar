/**
 * Copyright (c) 2018 Radboud University Nijmegen.
 * All rights reserved.
 *
 * @author Erwin R. Komen
 */

/*globals jQuery, crpstudio, Crpstudio, alert: false, */
var crpstudio = (function ($, crpstudio) {
  "use strict";
  crpstudio.htable = (function ($, config) {
    // Local variables within crpstudio.htable
    var bDebug = false,         // Debugging set or not
        level = 0,              // Recursion level of vertical draw tree
        loc_oNode = {},         // Local version of current node tree
        loc_errDiv = null,      // Where to show errors
        loc_iCurrentNode = -1,  // ID of the currently selected node
        loc_bKeep = false,      // Stay on fixed position
        loc_ht1 = "func-view",
        loc_ht2 = "func-name",
        loc_ht3 = "func-link",
        loc_ht4 = "func-inline",
        loc_ht5 = "func-plus",
        loc_ht6 = "arg-text",
        loc_ht7 = "arg-line",
        loc_ht8 = "arg-summary",
        loc_ht9 = "arg-endnode",
        loc_iTreeId = 0,
        loc_iMaxLevel = -1,
        root = null;            // Root of the tree (DOM position)

    // Methods that are local to [crpstudio.dbase]
    var private_methods = {
      /**
       * adapt_htable
       *      Recursively convert a htable to one that contains summaries
       *        and that contains level indicators
       *      The variable [loc_iMaxLevel] will in the end contain the maximum level
       * @param {object} oHtable
       * @returns {object}
       */
      adapt_htable: function (oHtable, iLevel, iParentId) {
        var summary = "", // Summary
            oBack = {},
            iParent = 0,
            iTreeId = 0,
            i,
            arChild = [];

        try {
          // Validate
          if (oHtable === undefined || oHtable === null) {
            return null;
          }
          // Get the level
          if (iLevel === undefined) { iLevel = 0; loc_iMaxLevel = -1; }
          // Possibly set tree id
          if ('id' in oHtable) {
            iTreeId = oHtable['id'];
          } else {
            iTreeId = private_methods.getTreeId();
            oHtable['id'] = iTreeId;
          }
          // Set my parentid
          if (iParentId !== undefined) {
            oHtable['parentid'] = iParentId;
          } else {
            oHtable['parentid'] = 0;
          }

          // Get text at this level
          if ('txt' in oHtable) {
            if ('type' in oHtable && oHtable['type'] !== "Star" && oHtable['type'] !== "Zero") {
              if (summary !== "") summary += " ";
              summary += oHtable['txt'];
            }
          }
          // Walk all the child tables
          if ('child' in oHtable) {
            arChild = oHtable['child'];
            for (i = 0; i < arChild.length; i++) {
              // First go down
              oBack = private_methods.adapt_htable(arChild[i], iLevel + 1, iTreeId);
              // Add the summary
              if ('summary' in oBack) {
                if (summary !== "") summary += " ";
                summary += oBack['summary'];
              }
            }
          }
          // Now set the summary link and the level
          oHtable['summary'] = summary;
          oHtable['level'] = iLevel;
          // Adapt the maxlevel
          if (iLevel > loc_iMaxLevel) { loc_iMaxLevel = iLevel;}
          // Return the adapted table
          return oHtable
        } catch (ex) {
          // Show the error at the indicated place
          private_methods.errMsg("adapt_htable", ex);
          return null;
        }
      },

      getTreeId: function () { loc_iTreeId += 1; return loc_iTreeId; },

      /**
       * render_htable
       *     Recursively convert a htable to an HTML string
       * @param {object} oHtable  - The table to be converted
       * @param {string} sLevel   - Either 'top' or 'descendant'
       * @returns {string}
       */
      render_htable: function(oHtable, sLevel) {
        var lHtml = [],
            oConstituent = {},
            oChild = {},
            sStretch = "",
            sText = "",
            sSign = "",
            sHidden = "",
            sColspanR = "",
            sColspanL = "",
            sRowClass = "",
            sTxtClass = "",
            arChild = [],
            arGchild = [],
            iLevel,
            j,
            i;

        try {
          // Retreive my level
          iLevel = oHtable['level'];

          // This is an end-node
          if (sLevel === "descendant") {
            // sStretch = "style=\"width: 100%;\"";
          }

          if (iLevel === 0) {
            // Start table
            lHtml.push("<table class=\"" + loc_ht1 + "\">");
          }

          // If this is top-level, then add a heading
          if (sLevel === "top") {
            lHtml.push("<thead><tr><th colspan=\""+(2 + loc_iMaxLevel)+"\">");
            // First span
            lHtml.push("<span class=\"" + loc_ht2 + "\">");
            lHtml.push("<a class=\"btn btn-xs btn-default "+loc_ht5+"\" " +
              "role=\"button\" " +
              "title=\"open\" " +
              "onclick=\"crpstudio.htable.htablehead_click(this, '" + loc_ht4 + "');\">");
            lHtml.push("+</a>");
            lHtml.push(oHtable['pos']);
            lHtml.push("</span>&nbsp;");
            // Second span
            lHtml.push("<span class=\"" + loc_ht3 + " pull-right\">");
            lHtml.push("<a class=\"btn btn-xs btn-default \" " +
              "role=\"button\" " +
              "title=\"copy to clipboard\" " +
              "onclick=\"crpstudio.htable.copy_click(this);\">");
            lHtml.push("<span class=\"glyphicon glyphicon-open\" aria-hidden=\"true\"></span>");
            lHtml.push("</a>");
            lHtml.push("</span>");
            // Finish the thead
            lHtml.push("</th></tr></thead>");
          }

          if (iLevel === 0) {
            // Start the table body
            lHtml.push("<tbody>");
          }

          if (iLevel > 0) {
            // Add the <tr> for myself first
            if (iLevel > 1) { sHidden = "class=\"hidden\""; }
            // sRowClass = " class=\"node-" + oHtable['id'] + " childof-" + oHtable['parentid'] + "\"";
            sRowClass = " nodeid=\"" + oHtable['id'] + "\" childof=\"" + oHtable['parentid'] + "\"";
            lHtml.push("<tr " + sHidden + sRowClass + ">");
            // [a] get the preceding <td> elements
            sColspanL = "colspan=\"" + (iLevel-1) + "\" ";
            if (iLevel > 1) { lHtml.push("<td class=\"arg-pre\" " + sColspanL + " style=\"min-width: " + (20 * (iLevel-1)) + "px;\" ></td>"); }
            // [b] Check if a '+' sign is needed
            if ('child' in oHtable) { sSign = "+"; } else { sSign = ""; }
            lHtml.push("<td class=\"arg-plus\" style=\"min-width: 20px;\" " +
              "onclick=\"crpstudio.htable.plus_click(this, '" + loc_ht4 + "');\">" + sSign + "</td>");
            // [c] Add the <td> for my own POS and summary
            sColspanR = "colspan=\"" + (loc_iMaxLevel - iLevel+1) + "\" ";
            lHtml.push("<td class=\"" + loc_ht6 + "\" " + sColspanR + sStretch + ">");
            lHtml.push("<span class=\"" + loc_ht7 + "\"><code>" + oHtable['pos'] + "</code></span>");
            // if ('txt' in oHtable) { sText = ""; } else { sText = oHtable['summary']; }
            // lHtml.push("<span class=\"" + loc_ht8 + "\">" + sText + "</span>");
            sTxtClass = ('txt' in oHtable) ? loc_ht9 : loc_ht8;
            lHtml.push("<span class=\"" + sTxtClass + "\">" + oHtable['summary'] + "</span>");
            lHtml.push("</td>");
            // [d] Add a <td> for the right part
            lHtml.push(" <td align=\"right\">");
            if ('txt' in oHtable) { sText = oHtable['txt']; } else { sText = ""; }
            lHtml.push("  <span>" + sText + "</span>");
            lHtml.push(" </td>");
            // Finish my own row
            lHtml.push("</tr>");
          }

          // Walk all 'child' elements -- if there are any
          if ('child' in oHtable) {
            arChild = oHtable['child'];
            for (i = 0; i < arChild.length; i++) {
              // Get access to this child - a non-end-node constituent
              oConstituent = arChild[i];
              // Add the output of this child
              lHtml.push(private_methods.render_htable(oConstituent, "descendant"));
            }
          }

          if (iLevel === 0) {
            // Finish the table body
            lHtml.push("</tbody>");

            // Finish the table
            lHtml.push("</table>");
          }

          // Combine into a string and return
          return lHtml.join("\n");
        } catch (ex) {
          // Show the error at the indicated place
          private_methods.errMsg("render_htable", ex);
          return "";
        }
      },

      /**
       * showError
       *     Show the error at the indicated place
       */
      errMsg: function (sFunction, ex) {
        var sOld = "",
            sMsg = "Error in " + sFunction + ": " + ex.message;

        if (loc_errDiv !== undefined && loc_errDiv !== null) {
          sOld = $(loc_errDiv).html();
          $(loc_errDiv).html(sOld + "<p><code>"+sMsg+"</code></p>");
        }
      },
      setErrLoc: function(sLoc) {
        loc_errDiv = sLoc;
        if (sLoc.indexOf("#")!==0) {
          loc_errDiv = "#" + loc_errDiv;
        }
        // Clear the errors
        $(loc_errDiv).html();
      },
      setNodeTree: function (oThis) {
        loc_oNode = oThis;
      }
    };

    // Methods that are exported by [crpstudio.htable] for outside functions
    return {
      /**
       * copy_click
       *     Copy HTML of table to clipboard
       * @param {div} elThis  - Division
       * @returns {void}
       */
      copy_click(elThis) {
        var elSel = null,
            $temp = $("<input>");

        // point to the current table
        elSel = $(elThis).closest("table");
        $("body").append($temp);
        $temp.val($(elSel).html()).select();
        document.execCommand("copy");
        $temp.remove();
      },
      ht_sign_plus : function(idx) {
        var sSign = $(this).html().trim();
        if (sSign === "-") {
          $(this).html("+");
        }
      },
      ht_sign_minus: function (idx) {
        var sSign = $(this).html().trim();
        if (sSign === "+") {
          $(this).html("-");
        } 
      },
      /**
       * htablehead_click
       *   Assuming we are on an element of class [func-plus]
       *     - close or open everything with style [sClass] below us
       *     - this depends on the 'sign' we have: + or -
       *   Also: adapt the +/- sign(s)
       */
      htablehead_click: function (el, sClass) {
        var trNext = null,
            elTbody = null, // My own <tbody>
            sStatus = "";   // My own status

        try {
          // Validate
          if (el === undefined) { return; }
          // Get my status
          sStatus = $(el).text().trim();   // This can be + or - or a SPACE
          // Get my own <tbody>
          elTbody = $(el).closest("table").children("tbody").first();
          // Check status
          if (sStatus === "-") {
            // We are open and need to close all below
            $(el).html("+");
            $(el).attr("title", "open");
            // Close all [arg-plus] below us
            $(elTbody).find(".arg-plus").each(crpstudio.htable.ht_sign_plus);
            $(elTbody).find(".func-plus").each(crpstudio.htable.ht_sign_plus);
            $(elTbody).find(".func-plus").attr("title", "open");
            $(elTbody).find(".func-inline").addClass("hidden");
            $(elTbody).find("tr").each(function (idx) {
              if ($(this).attr("childof") !== "1") {$(this).addClass("hidden");}
            });
            // All summaries may be shown
            $(elTbody).find(".arg-summary").removeClass("hidden");
          } else if (sStatus === "+") {
            // We are + (=closed) and need to open (become -)
            $(el).html("-");
            $(el).attr("title", "close");
            // Open all [arg-plus] below us
            $(elTbody).find(".arg-plus").each(crpstudio.htable.ht_sign_minus);
            $(elTbody).find(".func-plus").each(crpstudio.htable.ht_sign_minus);
            $(elTbody).find(".func-plus").attr("title", "close");
            $(elTbody).find(".func-inline").removeClass("hidden");
            $(elTbody).find("tr").removeClass("hidden");
            // No summaries must be shown
            $(elTbody).find(".arg-summary").addClass("hidden");
          }

        } catch (ex) {
          private_methods.errMsg("htablehead_click", ex);
        }
      },

      /**
       * plus_click
       *   Show or hide the <tr> elements under me, using 'nodeid' and 'childof'
       *   Also: 
       *    - adapt the +/- sign(s)
       *    - show the [arg-summary] part when sign is '+', otherwise hide it
       */
      plus_click: function (el, sClass, bShow) {
        var trNext = null,
            sStatus = "",
            elSummary = null,
            trMe = null,
            nodeid = 0;

        try {
          // Validate
          if (el === undefined) { return; }
          if ($(el).html().trim() === "") { return; }
          // Get my nodeid as INTEGER
          trMe = $(el).closest("tr");
          nodeid = $(trMe).attr("nodeid");
          // Get my status
          sStatus = $(el).html().trim();
          if (bShow !== undefined && bShow === false) {
            sStatus = "-";
          }
          // Get *ALL* the <tr> elements that are my direct children
          trNext = $(el).closest("tbody").find("tr");
          $(trNext).each(function (index) {
            if ($(this).attr("childof") === nodeid) {
              if (sStatus === "+" ) {
                // show it
                $(this).removeClass("hidden");
              } else {
                // hide it
                $(this).addClass("hidden");
                // Hide children too
                crpstudio.htable.plus_click($(this).find(".arg-plus").first(), loc_ht4, false);
              }
              if ($(this).hasClass("arg-grandchild")) {
                // hide it
                $(this).addClass("hidden");
              }
            }
          });
          // Find my own summary part
          elSummary = $(el).nextAll(".arg-text").find(".arg-summary").first();
          // Change my own status
          switch (sStatus) {
            case "+":
              $(el).html("-");
              // Hide the arg-summary
              $(elSummary).addClass("hidden");
              break;
            case "-":
              $(el).html("+");
              // Show the arg-summary
              $(elSummary).removeClass("hidden");
              break;
          }

        } catch (ex) {
          private_methods.errMsg("plus_click", ex);
        }
      },
      /**
       * treeToHtable
       *    Convert a JSON representation of a syntax tree to SVG
       * 
       * @param {element} htDiv   - DOM where tree must come
       * @param {object} oTree    - The tree as an object
       * @param {element} errDiv  - DOM where error may appear
       * @returns {boolean}
       */
      treeToHtable: function (htDiv, oTree, errDiv) {
        var sHtml = "",
            i;

        try {
          // Validate
          if (htDiv === undefined) return false;
          if (errDiv === undefined || errDiv === null) errDiv = htDiv;
          // Set the local error div
          private_methods.setErrLoc(errDiv);

          // Adapt the nodetree to contain 'summary' elements
          oTree = private_methods.adapt_htable(oTree);

          // Be sure to keep the tree locally
          private_methods.setNodeTree(oTree);

          // Create the html for this tree
          sHtml = private_methods.render_htable(oTree, "top");

          // Show the html in place
          $(htDiv).html(sHtml);

          // Attach an event handler to all the toggles
          //$(htDiv).find(".lithium-node").click(function () { crpstudio.htable.node_fix_svg(this) });

          // Return positively
          return true;
        } catch (ex) {
          // Show the error at the indicated place
          private_methods.errMsg("treeToHtable", ex);
          return null;
        }
      }

    }

  }($, crpstudio.config));

  return crpstudio;

}(jQuery, window.crpstudio || {}));
