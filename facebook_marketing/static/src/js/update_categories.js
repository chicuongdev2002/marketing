/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";

import { onMounted, onWillUpdateProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";

export class ListControllerExtend extends ListController {
  setup() {
    super.setup();
    this.orm = useService("orm");
  }

  async onClick_Update_Categories() {
    console.log(this)
    //this.env["ir.config_parameter"].sudo().set_param("facebook.api_token",document.getElementById("input").ariaValueMax)
    const result = await this.orm.call(
        'facebook.category',  // Tên của model
        'fetch_facebook_categories',  // Tên của hàm
        [],  // Danh sách các tham số positional
        {
            // Các tham số keyword nếu cần
        }
    );
    // await this.model.load();
    //         this.render();
    console.log("onClick_Update_Categories")
  }
}
ListControllerExtend.template = "facebook_marketing.list_test";

export class ListRendererExtend extends ListRenderer {
  setup() {
    super.setup();
    onMounted(() => {});
    onWillUpdateProps(async (nextProps) => {});
  }
}

registry.category("views").add("list_test", {
  ...listView,
  Controller: ListControllerExtend,
  Renderer: ListRendererExtend,
});
