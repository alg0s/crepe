import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import SetupView from "./SetupView.vue";

const loadSettings = vi.fn(async () => undefined);
const loadSystemStatus = vi.fn(async () => undefined);
const saveSettings = vi.fn(async () => undefined);
const runSettingsTest = vi.fn(async () => undefined);

vi.mock("../stores/app", () => ({
  useAppStore: () => ({
    state: {
      settings: {
        credential_source: "managed",
        external_env_path: null,
        managed_env_path: "/tmp/.config/crepe/.env",
        active_env_path: "/tmp/.config/crepe/.env",
        managed_credentials: { MS_TENANT_ID: true, MS_CLIENT_ID: true, MS_CLIENT_SECRET: true },
        effective_credentials: { MS_TENANT_ID: true, MS_CLIENT_ID: true, MS_CLIENT_SECRET: true },
        graph_auth_configured: true,
        missing_credentials: []
      },
      systemStatus: {
        graph_auth_configured: true,
        missing_credentials: [],
        credential_source: "managed",
        active_env_path: "/tmp/.config/crepe/.env"
      },
      settingsTest: null,
      error: ""
    },
    loadSettings,
    loadSystemStatus,
    saveSettings,
    runSettingsTest
  })
}));

describe("SetupView", () => {
  it("loads settings and triggers save/test actions", async () => {
    const wrapper = mount(SetupView);
    await nextTick();
    expect(loadSettings).toHaveBeenCalled();
    expect(loadSystemStatus).toHaveBeenCalled();
    expect(wrapper.text()).toContain("Configure Teams credentials");

    await wrapper.find("button.action-button").trigger("click");
    expect(saveSettings).toHaveBeenCalled();

    await wrapper.find("button.ghost-button").trigger("click");
    expect(runSettingsTest).toHaveBeenCalled();
  });
});
