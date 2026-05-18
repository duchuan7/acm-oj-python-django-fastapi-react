import React, { Component, StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { Alert, ConfigProvider } from "antd";
import "antd/dist/reset.css";
import App from "./App.jsx";
import "./styles.css";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Frontend render failed", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24 }}>
          <Alert
            type="error"
            showIcon
            message="Frontend render failed"
            description={this.state.error.message || String(this.state.error)}
          />
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#2f6f5e",
          colorInfo: "#2f6f5e",
          colorSuccess: "#3f7f5f",
          colorWarning: "#b7791f",
          colorError: "#b84a3a",
          colorText: "#1d2723",
          colorTextSecondary: "#6c766f",
          colorBgLayout: "#f6f3ec",
          colorBgContainer: "#fffdf8",
          colorBorder: "#e6ded1",
          borderRadius: 8,
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        },
        components: {
          Button: {
            controlHeight: 38,
            borderRadius: 8,
            primaryShadow: "none",
          },
          Card: {
            borderRadiusLG: 8,
            headerBg: "#fffdf8",
          },
          Layout: {
            headerBg: "#13231d",
            siderBg: "#fffdf8",
          },
          Menu: {
            itemBorderRadius: 8,
            itemSelectedBg: "#e8f1eb",
            itemSelectedColor: "#235446",
            itemHoverBg: "#f3eadb",
          },
          Table: {
            headerBg: "#f4efe5",
            headerColor: "#35423b",
            rowHoverBg: "#fbf6ec",
          },
          Tag: {
            borderRadiusSM: 6,
          },
        },
      }}
    >
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </ConfigProvider>
  </StrictMode>
);
