export interface paths {
    "/api/v1/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_api_v1_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/verify-email": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Email */
        post: operations["verify_email_api_v1_auth_verify_email_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/resend-verification": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resend Verification */
        post: operations["resend_verification_api_v1_auth_resend_verification_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh */
        post: operations["refresh_api_v1_auth_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_api_v1_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout-all": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout All */
        post: operations["logout_all_api_v1_auth_logout_all_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sessions */
        get: operations["list_sessions_api_v1_auth_sessions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Session */
        delete: operations["delete_session_api_v1_auth_sessions__session_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/forgot-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Forgot Password */
        post: operations["forgot_password_api_v1_auth_forgot_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/reset-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset Password */
        post: operations["reset_password_api_v1_auth_reset_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/change-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Password */
        post: operations["change_password_api_v1_auth_change_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/linkedin/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Linkedin Start */
        get: operations["linkedin_start_api_v1_auth_linkedin_start_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/linkedin/callback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Linkedin Callback */
        get: operations["linkedin_callback_api_v1_auth_linkedin_callback_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_api_v1_me_get"];
        put?: never;
        post?: never;
        /** Delete Me */
        delete: operations["delete_me_api_v1_me_delete"];
        options?: never;
        head?: never;
        /** Update Me */
        patch: operations["update_me_api_v1_me_patch"];
        trace?: never;
    };
    "/api/v1/me/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Request Data Export */
        post: operations["request_data_export_api_v1_me_export_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/export/{export_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download Data Export */
        get: operations["download_data_export_api_v1_me_export__export_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/connect": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Connect */
        post: operations["connect_api_v1_profile_connect_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/connect/callback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Connect Callback */
        get: operations["connect_callback_api_v1_profile_connect_callback_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/sync": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Sync */
        post: operations["sync_api_v1_profile_sync_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/sync/commit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Commit Sync */
        post: operations["commit_sync_api_v1_profile_sync_commit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/imports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Paste Import */
        post: operations["create_paste_import_api_v1_profile_imports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/imports/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Upload Import */
        post: operations["create_upload_import_api_v1_profile_imports_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/imports/{import_id}/commit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Commit Import */
        post: operations["commit_import_api_v1_profile_imports__import_id__commit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/snapshot": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Current Snapshot */
        get: operations["get_current_snapshot_api_v1_profile_snapshot_get"];
        /** Put Manual Snapshot */
        put: operations["put_manual_snapshot_api_v1_profile_snapshot_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/snapshots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Snapshots */
        get: operations["get_snapshots_api_v1_profile_snapshots_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/snapshots/{version_a}/diff/{version_b}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Snapshot Diff */
        get: operations["get_snapshot_diff_api_v1_profile_snapshots__version_a__diff__version_b__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/metrics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Gateway Metrics */
        get: operations["get_gateway_metrics_internal_metrics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/playground/prompts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Playground Prompts */
        get: operations["list_playground_prompts_internal_playground_prompts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/playground/run": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Run Playground Prompt */
        post: operations["run_playground_prompt_internal_playground_run_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/playground/stream": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Stream Playground Prompt */
        post: operations["stream_playground_prompt_internal_playground_stream_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/jobs/{job_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Job Status */
        get: operations["get_job_status_api_v1_jobs__job_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audits": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Audit */
        post: operations["start_audit_api_v1_audits_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audits/latest": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Latest */
        get: operations["get_latest_api_v1_audits_latest_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audits/{audit_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Audit */
        get: operations["get_audit_api_v1_audits__audit_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/scores/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Score History Endpoint */
        get: operations["get_score_history_endpoint_api_v1_scores_history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/recommendations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Recommendations */
        get: operations["get_recommendations_api_v1_recommendations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/recommendations/{recommendation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Recommendation */
        patch: operations["update_recommendation_api_v1_recommendations__recommendation_id__patch"];
        trace?: never;
    };
    "/api/v1/dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Dashboard */
        get: operations["get_dashboard_api_v1_dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tools */
        get: operations["list_tools_api_v1_tools_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/{tool_id}/run": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Run Tool */
        post: operations["run_tool_api_v1_tools__tool_id__run_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/{tool_id}/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tool Runs */
        get: operations["list_tool_runs_api_v1_tools__tool_id__runs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/runs/{run_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Tool Run
         * @description Single-run fetch -- the Workspace Hub's detail drawer uses this
         *     to show which tool produced a saved asset, with what inputs, so
         *     "open in tool" can re-run it.
         */
        get: operations["get_tool_run_api_v1_tools_runs__run_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/runs/{run_id}/regenerate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Regenerate Tool Run */
        post: operations["regenerate_tool_run_api_v1_tools_runs__run_id__regenerate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/runs/{run_id}/rate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Rate Tool Run */
        post: operations["rate_tool_run_api_v1_tools_runs__run_id__rate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/runs/{run_id}/save": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Save Tool Run */
        post: operations["save_tool_run_api_v1_tools_runs__run_id__save_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content/voice": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Voice Profile */
        get: operations["get_voice_profile_api_v1_content_voice_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content/voice/samples": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Pasted Samples */
        post: operations["submit_pasted_samples_api_v1_content_voice_samples_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content/voice/samples/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Uploaded Samples */
        post: operations["submit_uploaded_samples_api_v1_content_voice_samples_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Assets Endpoint */
        get: operations["list_assets_endpoint_api_v1_assets_get"];
        put?: never;
        /** Create Asset Endpoint */
        post: operations["create_asset_endpoint_api_v1_assets_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/{asset_id}/mark-posted": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Asset Posted */
        post: operations["mark_asset_posted_api_v1_assets__asset_id__mark_posted_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Carousel Endpoint */
        post: operations["create_carousel_endpoint_api_v1_carousels_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels/{asset_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Carousel Endpoint */
        get: operations["get_carousel_endpoint_api_v1_carousels__asset_id__get"];
        /** Update Carousel Endpoint */
        put: operations["update_carousel_endpoint_api_v1_carousels__asset_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels/{asset_id}/export/pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Carousel Pdf Endpoint */
        post: operations["export_carousel_pdf_endpoint_api_v1_carousels__asset_id__export_pdf_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels/{asset_id}/export/png": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Carousel Png Endpoint */
        post: operations["export_carousel_png_endpoint_api_v1_carousels__asset_id__export_png_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Plans Endpoint */
        get: operations["list_plans_endpoint_api_v1_content_plans_get"];
        put?: never;
        /** Create Plan Endpoint */
        post: operations["create_plan_endpoint_api_v1_content_plans_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/consistency": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Consistency Endpoint */
        get: operations["consistency_endpoint_api_v1_content_plans_consistency_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/performance-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Performance Summary Endpoint */
        get: operations["performance_summary_endpoint_api_v1_content_plans_performance_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Plan Endpoint */
        get: operations["get_plan_endpoint_api_v1_content_plans__plan_id__get"];
        put?: never;
        post?: never;
        /** Delete Plan Endpoint */
        delete: operations["delete_plan_endpoint_api_v1_content_plans__plan_id__delete"];
        options?: never;
        head?: never;
        /** Update Plan Endpoint */
        patch: operations["update_plan_endpoint_api_v1_content_plans__plan_id__patch"];
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/reschedule": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reschedule Plan Endpoint */
        post: operations["reschedule_plan_endpoint_api_v1_content_plans__plan_id__reschedule_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/reminder": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Set Reminder Endpoint */
        post: operations["set_reminder_endpoint_api_v1_content_plans__plan_id__reminder_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/mark-posted": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Posted Endpoint */
        post: operations["mark_posted_endpoint_api_v1_content_plans__plan_id__mark_posted_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/performance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Record Performance Endpoint */
        post: operations["record_performance_endpoint_api_v1_content_plans__plan_id__performance_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/recurring-slots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Recurring Slots Endpoint */
        post: operations["recurring_slots_endpoint_api_v1_content_plans_recurring_slots_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/bulk-schedule": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Bulk Schedule Endpoint */
        post: operations["bulk_schedule_endpoint_api_v1_content_plans_bulk_schedule_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/parse/paste": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Parse Resume Paste Endpoint */
        post: operations["parse_resume_paste_endpoint_api_v1_career_resumes_parse_paste_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/parse/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Parse Resume Upload Endpoint */
        post: operations["parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/from-profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Parse Resume From Profile Endpoint */
        post: operations["parse_resume_from_profile_endpoint_api_v1_career_resumes_from_profile_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Resumes Endpoint */
        get: operations["list_resumes_endpoint_api_v1_career_resumes_get"];
        put?: never;
        /** Commit Resume Endpoint */
        post: operations["commit_resume_endpoint_api_v1_career_resumes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Resume Endpoint */
        get: operations["get_resume_endpoint_api_v1_career_resumes__resume_id__get"];
        put?: never;
        post?: never;
        /** Delete Resume Endpoint */
        delete: operations["delete_resume_endpoint_api_v1_career_resumes__resume_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activate Resume Endpoint */
        post: operations["activate_resume_endpoint_api_v1_career_resumes__resume_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}/export/pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Resume Pdf Endpoint */
        post: operations["export_resume_pdf_endpoint_api_v1_career_resumes__resume_id__export_pdf_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}/export/docx": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Resume Docx Endpoint */
        post: operations["export_resume_docx_endpoint_api_v1_career_resumes__resume_id__export_docx_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/job-descriptions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Job Descriptions Endpoint */
        get: operations["list_job_descriptions_endpoint_api_v1_career_job_descriptions_get"];
        put?: never;
        /** Create Job Description Endpoint */
        post: operations["create_job_description_endpoint_api_v1_career_job_descriptions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/job-descriptions/{job_description_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Job Description Endpoint */
        get: operations["get_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__get"];
        put?: never;
        post?: never;
        /** Delete Job Description Endpoint */
        delete: operations["delete_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/matches": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Matches Endpoint */
        get: operations["list_matches_endpoint_api_v1_career_matches_get"];
        put?: never;
        /** Create Match Endpoint */
        post: operations["create_match_endpoint_api_v1_career_matches_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/growth/scores": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Scores Endpoint */
        get: operations["get_scores_endpoint_api_v1_growth_scores_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/growth/plan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Current Plan Endpoint */
        get: operations["get_current_plan_endpoint_api_v1_growth_plan_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/growth/plan/{plan_id}/items/{item_index}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Plan Item Endpoint */
        patch: operations["update_plan_item_endpoint_api_v1_growth_plan__plan_id__items__item_index__patch"];
        trace?: never;
    };
    "/api/v1/growth/goal": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Active Goal Endpoint */
        get: operations["get_active_goal_endpoint_api_v1_growth_goal_get"];
        put?: never;
        /** Start Goal Endpoint */
        post: operations["start_goal_endpoint_api_v1_growth_goal_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/growth/coach/conversation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Coach Conversation Endpoint
         * @description Gets or creates the user's one ongoing `mode="coach"` conversation
         *     -- the shared Assistant conversation store's answer to "which thread
         *     does /hubs/growth/coach open" (see docs/adr/0010). Sending and
         *     reading messages in it goes through the same generic
         *     `/api/v1/assistant/conversations/{id}/messages` endpoints every other
         *     conversation uses; this is the one growth-specific piece: knowing
         *     which conversation that is.
         */
        get: operations["get_coach_conversation_endpoint_api_v1_growth_coach_conversation_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/growth/coach/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Send Coach Message Endpoint
         * @description A convenience alias for sending into the coach conversation
         *     without the frontend first fetching its id -- routes through the same
         *     `orchestrator.handle_message` every conversation uses (mode="coach"
         *     dispatches straight to `coach_service.send_message`), so this still
         *     enforces the `assistant_messages` quota exactly like sending through
         *     `/api/v1/assistant/conversations/{coach_conversation_id}/messages`
         *     directly would.
         */
        post: operations["send_coach_message_endpoint_api_v1_growth_coach_messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/growth/scores/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Score History Endpoint */
        get: operations["get_score_history_endpoint_api_v1_growth_scores_history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/growth/before-after": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Before After Endpoint */
        get: operations["get_before_after_endpoint_api_v1_growth_before_after_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/trash": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Trash Endpoint */
        get: operations["list_trash_endpoint_api_v1_assets_trash_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/{asset_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Asset Endpoint */
        get: operations["get_asset_endpoint_api_v1_assets__asset_id__get"];
        put?: never;
        post?: never;
        /** Delete Asset Endpoint */
        delete: operations["delete_asset_endpoint_api_v1_assets__asset_id__delete"];
        options?: never;
        head?: never;
        /** Patch Asset Endpoint */
        patch: operations["patch_asset_endpoint_api_v1_assets__asset_id__patch"];
        trace?: never;
    };
    "/api/v1/assets/{asset_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restore Asset Endpoint */
        post: operations["restore_asset_endpoint_api_v1_assets__asset_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/{asset_id}/duplicate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Duplicate Asset Endpoint */
        post: operations["duplicate_asset_endpoint_api_v1_assets__asset_id__duplicate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/{asset_id}/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Versions Endpoint */
        get: operations["list_versions_endpoint_api_v1_assets__asset_id__versions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/{asset_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Export Asset Endpoint */
        get: operations["export_asset_endpoint_api_v1_assets__asset_id__export_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/bulk": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Bulk Action Endpoint */
        post: operations["bulk_action_endpoint_api_v1_assets_bulk_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/asset-folders": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Folders Endpoint */
        get: operations["list_folders_endpoint_api_v1_asset_folders_get"];
        put?: never;
        /** Create Folder Endpoint */
        post: operations["create_folder_endpoint_api_v1_asset_folders_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/asset-folders/{folder_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Folder Endpoint */
        delete: operations["delete_folder_endpoint_api_v1_asset_folders__folder_id__delete"];
        options?: never;
        head?: never;
        /** Update Folder Endpoint */
        patch: operations["update_folder_endpoint_api_v1_asset_folders__folder_id__patch"];
        trace?: never;
    };
    "/api/v1/assistant/suggested-prompts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Suggested Prompts */
        get: operations["get_suggested_prompts_api_v1_assistant_suggested_prompts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Conversations Endpoint */
        get: operations["list_conversations_endpoint_api_v1_assistant_conversations_get"];
        put?: never;
        /** Create Conversation Endpoint */
        post: operations["create_conversation_endpoint_api_v1_assistant_conversations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Conversation Endpoint */
        get: operations["get_conversation_endpoint_api_v1_assistant_conversations__conversation_id__get"];
        put?: never;
        post?: never;
        /** Delete Conversation Endpoint */
        delete: operations["delete_conversation_endpoint_api_v1_assistant_conversations__conversation_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/rename": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Rename Conversation Endpoint */
        post: operations["rename_conversation_endpoint_api_v1_assistant_conversations__conversation_id__rename_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/archive": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Archive Conversation Endpoint */
        post: operations["archive_conversation_endpoint_api_v1_assistant_conversations__conversation_id__archive_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/save": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Save Conversation Endpoint
         * @description Saves this conversation into Workspace as a `conversation` asset
         *     (the asset type Phase 05 already defined) -- a transcript of the
         *     active thread, not a live link, so it stays intact even if the
         *     conversation itself is later edited or deleted.
         */
        post: operations["save_conversation_endpoint_api_v1_assistant_conversations__conversation_id__save_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/context": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Context Settings Endpoint */
        get: operations["get_context_settings_endpoint_api_v1_assistant_conversations__conversation_id__context_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Context Settings Endpoint */
        patch: operations["update_context_settings_endpoint_api_v1_assistant_conversations__conversation_id__context_patch"];
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Send Message Endpoint */
        post: operations["send_message_endpoint_api_v1_assistant_conversations__conversation_id__messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/messages/{message_id}/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retry Message Endpoint */
        post: operations["retry_message_endpoint_api_v1_assistant_conversations__conversation_id__messages__message_id__retry_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/messages/{message_id}/edit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Edit Message Endpoint */
        post: operations["edit_message_endpoint_api_v1_assistant_conversations__conversation_id__messages__message_id__edit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/messages/{message_id}/rate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Rate Message Endpoint */
        post: operations["rate_message_endpoint_api_v1_assistant_conversations__conversation_id__messages__message_id__rate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assistant/conversations/{conversation_id}/confirm-tool": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirm Tool Endpoint */
        post: operations["confirm_tool_endpoint_api_v1_assistant_conversations__conversation_id__confirm_tool_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/pricing": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Pricing */
        get: operations["get_pricing_api_v1_billing_pricing_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/subscription": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Subscription */
        get: operations["get_subscription_api_v1_billing_subscription_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Payments */
        get: operations["list_payments_api_v1_billing_payments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/checkout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Checkout */
        post: operations["create_checkout_api_v1_billing_checkout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/portal": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Portal */
        post: operations["create_portal_api_v1_billing_portal_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel Subscription */
        post: operations["cancel_subscription_api_v1_billing_cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/change-plan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Plan */
        post: operations["change_plan_api_v1_billing_change_plan_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/webhooks/stripe": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Stripe Webhook */
        post: operations["stripe_webhook_api_v1_billing_webhooks_stripe_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/billing/webhooks/razorpay": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Razorpay Webhook */
        post: operations["razorpay_webhook_api_v1_billing_webhooks_razorpay_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notifications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Notifications Endpoint */
        get: operations["list_notifications_endpoint_api_v1_notifications_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notifications/{notification_id}/read": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Read Endpoint */
        post: operations["mark_read_endpoint_api_v1_notifications__notification_id__read_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notifications/read-all": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark All Read Endpoint */
        post: operations["mark_all_read_endpoint_api_v1_notifications_read_all_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notifications/preferences": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Preferences Endpoint */
        get: operations["get_preferences_endpoint_api_v1_notifications_preferences_get"];
        /** Set Preference Endpoint */
        put: operations["set_preference_endpoint_api_v1_notifications_preferences_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notifications/unsubscribe": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Unsubscribe Get */
        get: operations["unsubscribe_get_api_v1_notifications_unsubscribe_get"];
        put?: never;
        /**
         * Unsubscribe Post
         * @description RFC 8058 one-click unsubscribe: mail clients POST here directly
         *     (List-Unsubscribe-Post: List-Unsubscribe=One-Click) with no user
         *     interaction at all, so this must accept exactly the same token-only
         *     request the GET version does.
         */
        post: operations["unsubscribe_post_api_v1_notifications_unsubscribe_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Search Users Endpoint */
        get: operations["search_users_endpoint_api_v1_admin_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get User Detail Endpoint */
        get: operations["get_user_detail_endpoint_api_v1_admin_users__user_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/users/{user_id}/suspend": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Suspend User Endpoint */
        post: operations["suspend_user_endpoint_api_v1_admin_users__user_id__suspend_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/users/{user_id}/reinstate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reinstate User Endpoint */
        post: operations["reinstate_user_endpoint_api_v1_admin_users__user_id__reinstate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/users/{user_id}/force-password-reset": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Force Password Reset Endpoint */
        post: operations["force_password_reset_endpoint_api_v1_admin_users__user_id__force_password_reset_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/users/{user_id}/adjust-plan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Adjust Plan Endpoint */
        post: operations["adjust_plan_endpoint_api_v1_admin_users__user_id__adjust_plan_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/users/{user_id}/impersonate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Impersonate User Endpoint */
        post: operations["impersonate_user_endpoint_api_v1_admin_users__user_id__impersonate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/subscriptions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Subscriptions Endpoint */
        get: operations["list_subscriptions_endpoint_api_v1_admin_subscriptions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/subscriptions/{subscription_id}/webhooks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Webhook History Endpoint */
        get: operations["get_webhook_history_endpoint_api_v1_admin_subscriptions__subscription_id__webhooks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/webhooks/{webhook_event_id}/replay": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Replay Webhook Endpoint */
        post: operations["replay_webhook_endpoint_api_v1_admin_webhooks__webhook_event_id__replay_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/feature-flags": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Feature Flags Endpoint */
        get: operations["list_feature_flags_endpoint_api_v1_admin_feature_flags_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/feature-flags/{key}/global": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Set Flag Global Endpoint */
        post: operations["set_flag_global_endpoint_api_v1_admin_feature_flags__key__global_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/feature-flags/{key}/rollout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Set Flag Rollout Endpoint */
        post: operations["set_flag_rollout_endpoint_api_v1_admin_feature_flags__key__rollout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/feature-flags/{key}/user-override": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Set Flag User Override Endpoint */
        post: operations["set_flag_user_override_endpoint_api_v1_admin_feature_flags__key__user_override_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/ai-ops/overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ai Ops Overview Endpoint */
        get: operations["ai_ops_overview_endpoint_api_v1_admin_ai_ops_overview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/ai-ops/prompts/{prompt_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Prompt Drilldown Endpoint */
        get: operations["prompt_drilldown_endpoint_api_v1_admin_ai_ops_prompts__prompt_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/moderation/flags": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Moderation Flags Endpoint */
        get: operations["list_moderation_flags_endpoint_api_v1_admin_moderation_flags_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/moderation/flags/{flag_id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Review Moderation Flag Endpoint */
        post: operations["review_moderation_flag_endpoint_api_v1_admin_moderation_flags__flag_id__review_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/platform-health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Platform Health Endpoint */
        get: operations["platform_health_endpoint_api_v1_admin_platform_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/jobs/{job_id}/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retry Dead Job Endpoint */
        post: operations["retry_dead_job_endpoint_api_v1_admin_jobs__job_id__retry_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Ready
         * @description Liveness (`/health`) just confirms the process is up; this confirms
         *     it can actually serve traffic, by round-tripping the database -- what
         *     an uptime check and a deploy's readiness gate should both hit instead.
         */
        get: operations["ready_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AdjustPlanRequest */
        AdjustPlanRequest: {
            /** Plan */
            plan: string;
            /** Reason */
            reason: string;
        };
        /** AdminSubscriptionResponse */
        AdminSubscriptionResponse: {
            /** Id */
            id: string;
            /** User Id */
            user_id: string;
            /** Provider */
            provider: string;
            /** Plan */
            plan: string;
            /** Status */
            status: string;
            /** Current Period End */
            current_period_end: string | null;
            /** Cancel At Period End */
            cancel_at_period_end: boolean;
        };
        /** AdminSubscriptionSummary */
        AdminSubscriptionSummary: {
            /** Provider */
            provider: string;
            /** Plan */
            plan: string;
            /** Status */
            status: string;
            /** Current Period End */
            current_period_end: string | null;
        };
        /** AdminToolRunSummary */
        AdminToolRunSummary: {
            /** Id */
            id: string;
            /** Tool Id */
            tool_id: string;
            /** Status */
            status: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AdminUserDetailResponse */
        AdminUserDetailResponse: {
            user: components["schemas"]["AdminUserResponse"];
            subscription: components["schemas"]["AdminSubscriptionSummary"] | null;
            /** Recent Tool Runs */
            recent_tool_runs: components["schemas"]["AdminToolRunSummary"][];
            /** Ai Spend Minor This Month */
            ai_spend_minor_this_month: number;
            /** Ai Run Count This Month */
            ai_run_count_this_month: number;
        };
        /** AdminUserResponse */
        AdminUserResponse: {
            /** Id */
            id: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /** Plan */
            plan: string;
            /** Role */
            role: string;
            /** Status */
            status: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Last Login At */
            last_login_at: string | null;
        };
        /** AdminUserSearchResponse */
        AdminUserSearchResponse: {
            /** Items */
            items: components["schemas"]["AdminUserResponse"][];
            /** Total */
            total: number;
        };
        /** AiInvocationResponse */
        AiInvocationResponse: {
            /** Id */
            id: string;
            /** User Id */
            user_id: string;
            /** Prompt Id */
            prompt_id: string;
            /** Prompt Version */
            prompt_version: number;
            /** Tier */
            tier: string;
            /** Provider */
            provider: string;
            /** Model */
            model: string;
            /** Tokens In */
            tokens_in: number;
            /** Tokens Out */
            tokens_out: number;
            /** Cost Minor */
            cost_minor: number;
            /** Latency Ms */
            latency_ms: number;
            /** Cached */
            cached: boolean;
            /** Fallback Used */
            fallback_used: boolean;
            /** Outcome */
            outcome: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AiOpsOverviewResponse */
        AiOpsOverviewResponse: {
            /** Cost By Day */
            cost_by_day: components["schemas"]["CostByDayResponse"][];
            /** Cost By Model */
            cost_by_model: components["schemas"]["CostByDimensionResponse"][];
            /** Cost By Prompt */
            cost_by_prompt: components["schemas"]["CostByDimensionResponse"][];
            outcome_rates: components["schemas"]["OutcomeRatesResponse"];
            /** Slowest Prompts */
            slowest_prompts: components["schemas"]["SlowPromptResponse"][];
        };
        /** ArchiveConversationRequest */
        ArchiveConversationRequest: {
            /** Archived */
            archived: boolean;
        };
        /** AssetFolderCreateRequest */
        AssetFolderCreateRequest: {
            /** Name */
            name: string;
            /** Parent Id */
            parent_id?: string | null;
        };
        /** AssetFolderResponse */
        AssetFolderResponse: {
            /** Id */
            id: string;
            /** Name */
            name: string;
            /** Parent Id */
            parent_id: string | null;
        };
        /** AssetFolderUpdateRequest */
        AssetFolderUpdateRequest: {
            /** Name */
            name?: string | null;
            /** Parent Id */
            parent_id?: string | null;
            /**
             * Unfile
             * @default false
             */
            unfile: boolean;
        };
        /** AssetListResponse */
        AssetListResponse: {
            /** Items */
            items: components["schemas"]["WorkspaceAssetResponse"][];
            /** Next Cursor */
            next_cursor: string | null;
        };
        /** AssetPatchRequest */
        AssetPatchRequest: {
            /** Title */
            title?: string | null;
            /** Body */
            body?: string | null;
            /** Tags */
            tags?: string[] | null;
            /** Folder Id */
            folder_id?: string | null;
            /**
             * Unfile
             * @default false
             */
            unfile: boolean;
            /** Is Favourite */
            is_favourite?: boolean | null;
        };
        /** AssetResponse */
        AssetResponse: {
            /** Id */
            id: string;
            /** Type */
            type: string;
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Body Format */
            body_format: string;
            /** Source Tool Run Id */
            source_tool_run_id: string | null;
            /** Folder Id */
            folder_id: string | null;
            /** Metadata */
            metadata: {
                [key: string]: unknown;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * AssetType
         * @enum {string}
         */
        AssetType: "post" | "headline" | "about" | "experience_bullets" | "comment" | "message" | "resume" | "cover_letter" | "job_description" | "analysis" | "conversation" | "template" | "carousel" | "roadmap";
        /** AssetVersionResponse */
        AssetVersionResponse: {
            /** Version */
            version: number;
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Body Format */
            body_format: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AssistantMessageResponse */
        AssistantMessageResponse: {
            /** Id */
            id: string;
            /** Role */
            role: string;
            /** Content */
            content: string;
            /** Tool Call */
            tool_call: {
                [key: string]: unknown;
            } | null;
            /** Tool Run Id */
            tool_run_id: string | null;
            /** Parent Message Id */
            parent_message_id: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AuditCategoryResultResponse */
        AuditCategoryResultResponse: {
            /** Category */
            category: string;
            /** Score */
            score: number | null;
            /** Status */
            status: string;
            /** Inputs Available */
            inputs_available: {
                [key: string]: unknown;
            };
            /** Detail */
            detail: {
                [key: string]: unknown;
            };
            /** Findings */
            findings: components["schemas"]["AuditFindingResponse"][];
        };
        /** AuditDetailResponse */
        AuditDetailResponse: {
            /** Id */
            id: string;
            /** Status */
            status: string;
            /** Scoring Version */
            scoring_version: string;
            /** Overall Score */
            overall_score: number | null;
            /** Trigger */
            trigger: string;
            /** Started At */
            started_at: string | null;
            /** Completed At */
            completed_at: string | null;
            /** Duration Ms */
            duration_ms: number | null;
            /** Error */
            error: string | null;
            /** Categories */
            categories: components["schemas"]["AuditCategoryResultResponse"][];
        };
        /** AuditFindingResponse */
        AuditFindingResponse: {
            /** Id */
            id: string;
            /** Category */
            category: string;
            /** Code */
            code: string;
            /** Severity */
            severity: string;
            /** Title */
            title: string;
            /** Evidence */
            evidence: {
                [key: string]: unknown;
            };
            /** Deterministic */
            deterministic: boolean;
        };
        /** AuditRunRequest */
        AuditRunRequest: {
            /** Target Role */
            target_role?: string | null;
            /** Content History */
            content_history?: string[] | null;
        };
        /** AuditRunResponse */
        AuditRunResponse: {
            /** Job Id */
            job_id: string;
            /**
             * Audit Status
             * @default queued
             * @constant
             */
            audit_status: "queued";
        };
        /** BeforeAfterProfileEditResponse */
        BeforeAfterProfileEditResponse: {
            /** Version */
            version: number;
            /** Source */
            source: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** BeforeAfterResponse */
        BeforeAfterResponse: {
            /**
             * From Date
             * Format: date
             */
            from_date: string;
            /**
             * To Date
             * Format: date
             */
            to_date: string;
            /** Score Deltas */
            score_deltas: components["schemas"]["ScoreDeltaResponse"][];
            /** Tool Runs */
            tool_runs: components["schemas"]["BeforeAfterToolRunResponse"][];
            /** Profile Edits */
            profile_edits: components["schemas"]["BeforeAfterProfileEditResponse"][];
        };
        /** BeforeAfterToolRunResponse */
        BeforeAfterToolRunResponse: {
            /** Tool Id */
            tool_id: string;
            /** Status */
            status: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** Body_create_upload_import_api_v1_profile_imports_upload_post */
        Body_create_upload_import_api_v1_profile_imports_upload_post: {
            /** File */
            file: string;
        };
        /** Body_parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post */
        Body_parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post: {
            /** File */
            file: string;
        };
        /** Body_submit_uploaded_samples_api_v1_content_voice_samples_upload_post */
        Body_submit_uploaded_samples_api_v1_content_voice_samples_upload_post: {
            /** File */
            file: string;
        };
        /** BulkActionRequest */
        BulkActionRequest: {
            /**
             * Action
             * @enum {string}
             */
            action: "move" | "tag" | "delete" | "export";
            /** Asset Ids */
            asset_ids: string[];
            /** Folder Id */
            folder_id?: string | null;
            /** Tags */
            tags?: string[] | null;
            /**
             * Format
             * @default txt
             * @enum {string}
             */
            format: "txt" | "md" | "pdf" | "docx";
        };
        /** BulkActionResponse */
        BulkActionResponse: {
            /** Affected Count */
            affected_count: number;
        };
        /** BulkScheduleRequest */
        BulkScheduleRequest: {
            cadence: components["schemas"]["Cadence"];
            /** Plan Ids */
            plan_ids: string[];
        };
        /** Cadence */
        Cadence: {
            /**
             * Days Of Week
             * @description 0=Monday ... 6=Sunday
             */
            days_of_week: number[];
            /** Time */
            time?: string | null;
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
            /** Weeks */
            weeks: number;
        };
        /** CancelSubscriptionRequest */
        CancelSubscriptionRequest: {
            /**
             * At Period End
             * @default true
             */
            at_period_end: boolean;
            /** Reason */
            reason?: string | null;
        };
        /** CarouselClosing */
        CarouselClosing: {
            /**
             * Cta
             * @default
             */
            cta: string;
        };
        /** CarouselCover */
        CarouselCover: {
            /** Headline */
            headline: string;
            /**
             * Subhead
             * @default
             */
            subhead: string;
        };
        /**
         * CarouselData
         * @description The carousel's re-editable structure -- stored as `Asset.body`
         *     (JSON) so the slide-by-slide editor can load it back exactly.
         */
        CarouselData: {
            /**
             * Template
             * @default clean
             * @enum {string}
             */
            template: "clean" | "bold" | "minimal";
            cover: components["schemas"]["CarouselCover"];
            /** Slides */
            slides: components["schemas"]["CarouselSlide"][];
            closing?: components["schemas"]["CarouselClosing"];
            /**
             * Caption
             * @default
             */
            caption: string;
        };
        /** CarouselResponse */
        CarouselResponse: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            data: components["schemas"]["CarouselData"];
        };
        /** CarouselSlide */
        CarouselSlide: {
            /** Headline */
            headline: string;
            /** Body */
            body: string;
            /**
             * Visual Note
             * @default
             */
            visual_note: string;
        };
        /** Certification */
        Certification: {
            /** Name */
            name?: string | null;
            /** Issuer */
            issuer?: string | null;
            issued?: components["schemas"]["DatePart"] | null;
            /** Credential Id */
            credential_id?: string | null;
            /** Url */
            url?: string | null;
        };
        /** ChangePasswordRequest */
        ChangePasswordRequest: {
            /** Current Password */
            current_password: string;
            /** New Password */
            new_password: string;
        };
        /** ChangePlanRequest */
        ChangePlanRequest: {
            /**
             * Plan
             * @enum {string}
             */
            plan: "free" | "pro";
            /**
             * Interval
             * @default month
             * @enum {string}
             */
            interval: "month" | "year";
        };
        /** CheckoutRequest */
        CheckoutRequest: {
            /**
             * Plan
             * @enum {string}
             */
            plan: "free" | "pro";
            /**
             * Interval
             * @default month
             * @enum {string}
             */
            interval: "month" | "year";
        };
        /** CheckoutResponse */
        CheckoutResponse: {
            /** Checkout Url */
            checkout_url: string;
        };
        /** CommitImportRequest */
        CommitImportRequest: {
            payload: components["schemas"]["ProfileSnapshot"];
        };
        /** CommitResumeRequest */
        CommitResumeRequest: {
            /** Title */
            title: string;
            /** Source */
            source: string;
            document: components["schemas"]["ResumeDocument"];
            /** Original File Ref */
            original_file_ref?: string | null;
        };
        /** ConfirmToolRunRequest */
        ConfirmToolRunRequest: {
            /**
             * Message Id
             * Format: uuid
             */
            message_id: string;
            /** Tool Id */
            tool_id: string;
            /** Input */
            input: {
                [key: string]: unknown;
            };
        };
        /** ConsistencyWeek */
        ConsistencyWeek: {
            /**
             * Week Start
             * Format: date
             */
            week_start: string;
            /** Posted Count */
            posted_count: number;
        };
        /** ContentPlanCreate */
        ContentPlanCreate: {
            /** Asset Id */
            asset_id?: string | null;
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Body Preview
             * @default
             */
            body_preview: string;
            /**
             * Content Type
             * @default post
             */
            content_type: string;
            /**
             * Status
             * @default idea
             * @enum {string}
             */
            status: "idea" | "drafted" | "ready" | "scheduled" | "posted" | "skipped";
            /**
             * Planned For
             * Format: date
             */
            planned_for: string;
            /** Planned Time */
            planned_time?: string | null;
            /** Tags */
            tags?: string[];
            /**
             * Notes
             * @default
             */
            notes: string;
        };
        /** ContentPlanResponse */
        ContentPlanResponse: {
            /** Id */
            id: string;
            /** Asset Id */
            asset_id: string | null;
            /** Title */
            title: string;
            /** Body Preview */
            body_preview: string;
            /** Content Type */
            content_type: string;
            /**
             * Status
             * @enum {string}
             */
            status: "idea" | "drafted" | "ready" | "scheduled" | "posted" | "skipped";
            /**
             * Planned For
             * Format: date
             */
            planned_for: string;
            /** Planned Time */
            planned_time: string | null;
            /** Posted At */
            posted_at: string | null;
            /** Reminder At */
            reminder_at: string | null;
            /** Recurrence Rule */
            recurrence_rule: string | null;
            /** Tags */
            tags: string[];
            /** Performance */
            performance: {
                [key: string]: number | string;
            };
            /** Notes */
            notes: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ContentPlanUpdate */
        ContentPlanUpdate: {
            /** Title */
            title?: string | null;
            /** Body Preview */
            body_preview?: string | null;
            /** Content Type */
            content_type?: string | null;
            /** Status */
            status?: ("idea" | "drafted" | "ready" | "scheduled" | "posted" | "skipped") | null;
            /** Tags */
            tags?: string[] | null;
            /** Notes */
            notes?: string | null;
        };
        /** ContextItemResponse */
        ContextItemResponse: {
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Excluded */
            excluded: boolean;
        };
        /** ContextSettingsResponse */
        ContextSettingsResponse: {
            /** Items */
            items: components["schemas"]["ContextItemResponse"][];
        };
        /** ContextTogglesRequest */
        ContextTogglesRequest: {
            /** Excluded Context Keys */
            excluded_context_keys: string[];
        };
        /** ConversationCreate */
        ConversationCreate: {
            /**
             * Mode
             * @default auto
             * @enum {string}
             */
            mode: "auto" | "tool";
            /** Tool Id */
            tool_id?: string | null;
        };
        /** ConversationDetailResponse */
        ConversationDetailResponse: {
            conversation: components["schemas"]["ConversationSummary"];
            /** Messages */
            messages: components["schemas"]["AssistantMessageResponse"][];
        };
        /** ConversationSummary */
        ConversationSummary: {
            /** Id */
            id: string;
            /** Title */
            title: string | null;
            /** Mode */
            mode: string;
            /** Message Count */
            message_count: number;
            /** Last Message At */
            last_message_at: string | null;
            /** Is Archived */
            is_archived: boolean;
            /** Asset Id */
            asset_id: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** CostByDayResponse */
        CostByDayResponse: {
            /**
             * Day
             * Format: date
             */
            day: string;
            /** Cost Minor */
            cost_minor: number;
            /** Tokens In */
            tokens_in: number;
            /** Tokens Out */
            tokens_out: number;
            /** Invocation Count */
            invocation_count: number;
        };
        /** CostByDimensionResponse */
        CostByDimensionResponse: {
            /** Key */
            key: string;
            /** Cost Minor */
            cost_minor: number;
            /** Invocation Count */
            invocation_count: number;
        };
        /** CreateAssetRequest */
        CreateAssetRequest: {
            /** @default post */
            type: components["schemas"]["AssetType"];
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Folder Id */
            folder_id?: string | null;
        };
        /** CreateResumeMatchRequest */
        CreateResumeMatchRequest: {
            /** Resume Id */
            resume_id: string;
            /** Job Description Id */
            job_description_id: string;
        };
        /** DashboardHealthScore */
        DashboardHealthScore: {
            /** Audit Id */
            audit_id: string;
            /** Overall */
            overall: number | null;
            /** Scoring Version */
            scoring_version: string;
            /** Status */
            status: string;
            /** Completed At */
            completed_at: string | null;
            /** Categories */
            categories: components["schemas"]["AuditCategoryResultResponse"][];
        };
        /** DashboardResponse */
        DashboardResponse: {
            user: components["schemas"]["DashboardUser"];
            /** Is First Time */
            is_first_time: boolean;
            health_score: components["schemas"]["DashboardHealthScore"] | null;
            score_history: components["schemas"]["DashboardScoreHistory"];
            /** Top Recommendations */
            top_recommendations: components["schemas"]["RecommendationResponse"][];
            run_audit: components["schemas"]["DashboardRunAuditState"];
            /** Hubs */
            hubs: {
                [key: string]: boolean;
            };
        };
        /** DashboardRunAuditState */
        DashboardRunAuditState: {
            /** Can Run */
            can_run: boolean;
            /** Reason */
            reason: ("no_active_snapshot" | "audit_in_progress" | "cooldown_active" | "quota_exceeded") | null;
            /** Retry After Seconds */
            retry_after_seconds: number | null;
            /** In Flight Job Id */
            in_flight_job_id: string | null;
            /** Quota Used */
            quota_used: number;
            /** Quota Limit */
            quota_limit: number;
        };
        /** DashboardScoreHistory */
        DashboardScoreHistory: {
            /** Range */
            range: string;
            /** Points */
            points: components["schemas"]["ScoreHistoryPoint"][];
            /** Delta */
            delta: number | null;
        };
        /** DashboardUser */
        DashboardUser: {
            /** Full Name */
            full_name: string;
            /** Plan */
            plan: string;
        };
        /**
         * DatePart
         * @description A partial date as LinkedIn and resumes actually give it to us.
         */
        DatePart: {
            /** Year */
            year?: number | null;
            /** Month */
            month?: number | null;
        };
        /** DeleteAccountRequest */
        DeleteAccountRequest: {
            /** Current Password */
            current_password?: string | null;
        };
        /** EditMessageRequest */
        EditMessageRequest: {
            /** Text */
            text: string;
        };
        /** Education */
        Education: {
            /** School */
            school?: string | null;
            /** Degree */
            degree?: string | null;
            /** Field */
            field?: string | null;
            /** Start Year */
            start_year?: number | null;
            /** End Year */
            end_year?: number | null;
            /** Description */
            description?: string | null;
        };
        /** Experience */
        Experience: {
            /** Company */
            company?: string | null;
            /** Title */
            title?: string | null;
            /** Employment Type */
            employment_type?: string | null;
            /** Location */
            location?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
            /** Is Current */
            is_current?: boolean | null;
            /** Description */
            description?: string | null;
            /** Bullets */
            bullets?: string[] | null;
            /** Skills */
            skills?: string[] | null;
        };
        /** ExportJobResponse */
        ExportJobResponse: {
            /** Job Id */
            job_id: string;
        };
        /** FeatureFlagResponse */
        FeatureFlagResponse: {
            /** Key */
            key: string;
            /** Enabled Globally */
            enabled_globally: boolean;
            /** Rollout Percent */
            rollout_percent: number;
            /** Description */
            description: string | null;
        };
        /** FieldChange */
        FieldChange: {
            /** Path */
            path: string;
            /** Before */
            before: unknown | null;
            /** After */
            after: unknown | null;
        };
        /** FieldProvenance */
        FieldProvenance: {
            source: components["schemas"]["ProfileSource"];
            /** Confidence */
            confidence: number;
        };
        /** ForcePasswordResetResponse */
        ForcePasswordResetResponse: {
            /** Reset Token */
            reset_token: string;
        };
        /** ForgotPasswordRequest */
        ForgotPasswordRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
        };
        /** GatewayMetricsResponse */
        GatewayMetricsResponse: {
            /** Window Hours */
            window_hours: number;
            /** Total Invocations */
            total_invocations: number;
            /** Latency P50 Ms */
            latency_p50_ms: number | null;
            /** Latency P95 Ms */
            latency_p95_ms: number | null;
            /** Cache Hit Rate */
            cache_hit_rate: number | null;
            /** Fallback Rate */
            fallback_rate: number | null;
            /** Invalid Output Rate */
            invalid_output_rate: number | null;
            /** Cost Per User Per Day Minor */
            cost_per_user_per_day_minor: {
                [key: string]: number;
            };
        };
        /** GrowthGoalCreate */
        GrowthGoalCreate: {
            /** Goal Type */
            goal_type: string;
            /** Target Role */
            target_role?: string | null;
            /**
             * Target Description
             * @default
             */
            target_description: string;
            /** Horizon Weeks */
            horizon_weeks: number;
        };
        /** GrowthGoalResponse */
        GrowthGoalResponse: {
            /** Id */
            id: string;
            /** Goal Type */
            goal_type: string;
            /** Target Role */
            target_role: string | null;
            /** Target Description */
            target_description: string;
            /** Horizon Weeks */
            horizon_weeks: number;
            /**
             * Started At
             * Format: date-time
             */
            started_at: string;
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "completed" | "abandoned";
            /** Baseline Scores */
            baseline_scores: {
                [key: string]: unknown;
            };
        };
        /** GrowthScoreHistoryResponse */
        GrowthScoreHistoryResponse: {
            /** Health */
            health: components["schemas"]["ScoreHistoryPointResponse"][];
            /** Visibility */
            visibility: components["schemas"]["ScoreHistoryPointResponse"][];
            /** Consistency */
            consistency: components["schemas"]["ScoreHistoryPointResponse"][];
            /** Personal Branding */
            personal_branding: components["schemas"]["ScoreHistoryPointResponse"][];
        };
        /** GrowthScoreResponse */
        GrowthScoreResponse: {
            /** Score Type */
            score_type: string;
            /** Value */
            value: number | null;
            /** Status */
            status: string;
            /** Components */
            components: components["schemas"]["ScoreComponentResponse"][];
            /**
             * Computed At
             * Format: date-time
             */
            computed_at: string;
            /** Scoring Version */
            scoring_version: string;
            /** Needed */
            needed: {
                [key: string]: unknown;
            } | null;
        };
        /** GrowthScoresResponse */
        GrowthScoresResponse: {
            health: components["schemas"]["GrowthScoreResponse"];
            visibility: components["schemas"]["GrowthScoreResponse"];
            consistency: components["schemas"]["GrowthScoreResponse"];
            personal_branding: components["schemas"]["GrowthScoreResponse"];
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /**
         * Hub
         * @enum {string}
         */
        Hub: "profile" | "content" | "engagement" | "career" | "growth";
        /** Identity */
        Identity: {
            /** Full Name */
            full_name?: string | null;
            /** Headline */
            headline?: string | null;
            /** Custom Url */
            custom_url?: string | null;
            /** Industry */
            industry?: string | null;
            /** Location */
            location?: string | null;
            /** Profile Picture Url */
            profile_picture_url?: string | null;
        };
        /** ImpersonateResponse */
        ImpersonateResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
        };
        /** ImportPasteRequest */
        ImportPasteRequest: {
            /** Text */
            text: string;
        };
        /** ImportResponse */
        ImportResponse: {
            /** Import Id */
            import_id: string;
            /** Status */
            status: string;
            draft?: components["schemas"]["ProfileSnapshot"] | null;
            /**
             * Parse Warnings
             * @default []
             */
            parse_warnings: string[];
            /** Error */
            error?: string | null;
        };
        /** JobDescriptionParseRequest */
        JobDescriptionParseRequest: {
            /** Title */
            title: string;
            /** Company */
            company?: string | null;
            /** Raw Text */
            raw_text: string;
        };
        /** JobDescriptionResponse */
        JobDescriptionResponse: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            /** Company */
            company: string | null;
            /** Source */
            source: string;
            /** Raw Text */
            raw_text: string;
            /** Parsed */
            parsed: {
                [key: string]: unknown;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** JobResponse */
        JobResponse: {
            /** Id */
            id: string;
            /** Type */
            type: string;
            /** Status */
            status: string;
            /** Attempts */
            attempts: number;
            /** Error */
            error: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Finished At */
            finished_at: string | null;
        };
        /** JobStatusResponse */
        JobStatusResponse: {
            /** Id */
            id: string;
            /** Type */
            type: string;
            /** Status */
            status: string;
            /** Attempts */
            attempts: number;
            /** Max Attempts */
            max_attempts: number;
            /** Progress Percent */
            progress_percent: number;
            /** Error */
            error: string | null;
            /** Result */
            result: {
                [key: string]: unknown;
            } | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Started At */
            started_at: string | null;
            /** Finished At */
            finished_at: string | null;
        };
        /** Language */
        Language: {
            /** Name */
            name?: string | null;
            /** Proficiency */
            proficiency?: string | null;
        };
        /** LinkedInStartResponse */
        LinkedInStartResponse: {
            /** Authorization Url */
            authorization_url: string;
        };
        /** ListItemChange */
        ListItemChange: {
            /** Key */
            key: string;
            /** Change */
            change: string;
            /** Before */
            before?: {
                [key: string]: unknown;
            } | null;
            /** After */
            after?: {
                [key: string]: unknown;
            } | null;
            /**
             * Field Changes
             * @default []
             */
            field_changes: components["schemas"]["FieldChange"][];
        };
        /** LoginRequest */
        LoginRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
        };
        /** LoginResponse */
        LoginResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
            /** Expires In */
            expires_in: number;
            user: components["schemas"]["UserPublic"];
        };
        /** MarkContentPlanPostedRequest */
        MarkContentPlanPostedRequest: {
            /** Linkedin Url */
            linkedin_url?: string | null;
            /** Posted At */
            posted_at?: string | null;
            performance?: components["schemas"]["PerformanceNumbers"] | null;
        };
        /** MarkPostedRequest */
        MarkPostedRequest: {
            /** Linkedin Url */
            linkedin_url?: string | null;
        };
        /** MeResponse */
        MeResponse: {
            user: components["schemas"]["UserPublic"];
            /** Feature Flags */
            feature_flags: {
                [key: string]: boolean;
            };
        };
        /** MessageResponse */
        MessageResponse: {
            /** Message */
            message: string;
        };
        /** Metrics */
        Metrics: {
            /** Connections */
            connections?: number | null;
            /** Followers */
            followers?: number | null;
            /** Recommendations Received */
            recommendations_received?: number | null;
        };
        /** ModerationFlagResponse */
        ModerationFlagResponse: {
            /** Id */
            id: string;
            /** User Id */
            user_id: string;
            /** Source */
            source: string;
            /** Target Type */
            target_type: string;
            /** Target Id */
            target_id: string;
            /** Reason */
            reason: string;
            /** Excerpt */
            excerpt: string;
            /** Status */
            status: string;
            /** Reviewed By */
            reviewed_by: string | null;
            /** Reviewed At */
            reviewed_at: string | null;
            /** Review Note */
            review_note: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** NotificationListResponse */
        NotificationListResponse: {
            /** Items */
            items: components["schemas"]["NotificationResponse"][];
            /** Unread Count */
            unread_count: number;
        };
        /** NotificationResponse */
        NotificationResponse: {
            /** Id */
            id: string;
            /** Type */
            type: string;
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Action Route */
            action_route: string | null;
            /** Metadata */
            metadata: {
                [key: string]: unknown;
            };
            /** Read At */
            read_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** OutcomeRatesResponse */
        OutcomeRatesResponse: {
            /** Total */
            total: number;
            /** Invalid Output Rate */
            invalid_output_rate: number;
            /** Fallback Rate */
            fallback_rate: number;
            /** Policy Blocked Rate */
            policy_blocked_rate: number;
            /** Provider Error Rate */
            provider_error_rate: number;
        };
        /** PaymentResponse */
        PaymentResponse: {
            /** Id */
            id: string;
            /** Amount Minor */
            amount_minor: number;
            /** Currency */
            currency: string;
            /** Status */
            status: string;
            /** Failure Reason */
            failure_reason: string | null;
            /** Invoice Url */
            invoice_url: string | null;
            /** Paid At */
            paid_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** PerformanceNumbers */
        PerformanceNumbers: {
            /** Impressions */
            impressions?: number | null;
            /** Reactions */
            reactions?: number | null;
            /** Comments */
            comments?: number | null;
            /** Reposts */
            reposts?: number | null;
            /** Profile Views */
            profile_views?: number | null;
        };
        /** PerformanceSummaryResponse */
        PerformanceSummaryResponse: {
            /** Sufficient Data */
            sufficient_data: boolean;
            /** Total Data Points */
            total_data_points: number;
            /** By Content Type */
            by_content_type: components["schemas"]["PostTypePerformance"][];
        };
        /** PlanLimitResponse */
        PlanLimitResponse: {
            /**
             * Plan
             * @enum {string}
             */
            plan: "free" | "pro";
            /** Metric */
            metric: string;
            /** Limit Value */
            limit_value: number;
            /** Window */
            window: string;
            /** Overage Behaviour */
            overage_behaviour: string;
        };
        /** PlatformHealthResponse */
        PlatformHealthResponse: {
            queue_depth: components["schemas"]["QueueDepthResponse"];
            /** Dead Jobs */
            dead_jobs: components["schemas"]["JobResponse"][];
            /** Circuit Breakers */
            circuit_breakers: {
                [key: string]: {
                    [key: string]: unknown;
                };
            };
        };
        /** PlaygroundPromptSummary */
        PlaygroundPromptSummary: {
            /** Id */
            id: string;
            /** Version */
            version: number;
            /** Tier */
            tier: string;
            /** Description */
            description: string;
            /** Required Context */
            required_context: string[];
            /** Output Schema */
            output_schema: {
                [key: string]: unknown;
            } | null;
            /** Max Output Tokens */
            max_output_tokens: number;
            /** Temperature */
            temperature: number;
            /** Cache Ttl Seconds */
            cache_ttl_seconds: number;
        };
        /** PlaygroundRunRequest */
        PlaygroundRunRequest: {
            /** Prompt Id */
            prompt_id: string;
            /** Context */
            context: {
                [key: string]: string;
            };
            /** Tier Override */
            tier_override?: string | null;
        };
        /** PlaygroundRunResponse */
        PlaygroundRunResponse: {
            /** Text */
            text: string | null;
            /** Parsed */
            parsed: unknown | null;
            /** Model */
            model: string;
            /** Provider */
            provider: string;
            /** Tokens In */
            tokens_in: number;
            /** Tokens Out */
            tokens_out: number;
            /** Cost Minor */
            cost_minor: number;
            /** Currency */
            currency: string;
            /** Latency Ms */
            latency_ms: number;
            /** Cached */
            cached: boolean;
            /** Fallback Used */
            fallback_used: boolean;
            /** Correlation Id */
            correlation_id: string;
        };
        /** PortalResponse */
        PortalResponse: {
            /** Portal Url */
            portal_url: string;
        };
        /** PostTypePerformance */
        PostTypePerformance: {
            /** Content Type */
            content_type: string;
            /** Sample Size */
            sample_size: number;
            /** Median Engagement */
            median_engagement: number;
        };
        /** PreferenceRow */
        PreferenceRow: {
            /**
             * Channel
             * @enum {string}
             */
            channel: "in_app" | "email";
            /** Type */
            type: string;
            /** Enabled */
            enabled: boolean;
        };
        /** PreferencesResponse */
        PreferencesResponse: {
            /** Preferences */
            preferences: components["schemas"]["PreferenceRow"][];
        };
        /**
         * PricingResponse
         * @description Built straight from `plan_limits` (see app/routers/billing.py) so
         *     the pricing page can never drift from what the app actually enforces.
         */
        PricingResponse: {
            /** Limits */
            limits: components["schemas"]["PlanLimitResponse"][];
            /** Currency */
            currency: string;
        };
        /**
         * ProfileSnapshot
         * @description The one canonical shape every input path must converge on.
         */
        ProfileSnapshot: {
            /**
             * Version
             * @default 1
             */
            version: number;
            source: components["schemas"]["ProfileSource"];
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            identity?: components["schemas"]["Identity"] | null;
            /** About */
            about?: string | null;
            /** Experiences */
            experiences?: components["schemas"]["Experience"][] | null;
            /** Education */
            education?: components["schemas"]["Education"][] | null;
            /** Skills */
            skills?: components["schemas"]["Skill"][] | null;
            /** Certifications */
            certifications?: components["schemas"]["Certification"][] | null;
            /** Languages */
            languages?: components["schemas"]["Language"][] | null;
            /** Projects */
            projects?: components["schemas"]["Project"][] | null;
            metrics?: components["schemas"]["Metrics"] | null;
            /** Field Provenance */
            field_provenance?: {
                [key: string]: components["schemas"]["FieldProvenance"];
            };
        };
        /**
         * ProfileSource
         * @enum {string}
         */
        ProfileSource: "linkedin_api" | "paste" | "upload_pdf" | "upload_docx" | "manual" | "merged";
        /** Project */
        Project: {
            /** Name */
            name?: string | null;
            /** Description */
            description?: string | null;
            /** Url */
            url?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
        };
        /**
         * ProvenanceSource
         * @description Where one field of a parsed ResumeDocument came from -- distinct
         *     from `ResumeSource` (which describes the whole document): a single
         *     upload can still have most fields parsed deterministically and a
         *     handful resolved by the one-shot AI pass for ambiguous segments.
         * @enum {string}
         */
        ProvenanceSource: "deterministic_parse" | "ai_resolved" | "user_edited" | "built" | "imported_from_profile";
        /** QueueDepthResponse */
        QueueDepthResponse: {
            /** Queued */
            queued: number;
            /** Leased */
            leased: number;
            /** Dead */
            dead: number;
            /** Failed Last Hour */
            failed_last_hour: number;
        };
        /** QuotaInfo */
        QuotaInfo: {
            /** Metric */
            metric: string;
            /** Used */
            used: number;
            /** Limit */
            limit: number;
        };
        /** RateMessageRequest */
        RateMessageRequest: {
            /**
             * Rating
             * @enum {string}
             */
            rating: "up" | "down";
        };
        /** RateRequest */
        RateRequest: {
            /**
             * Rating
             * @enum {string}
             */
            rating: "up" | "down";
            /** Feedback Text */
            feedback_text?: string | null;
        };
        /** RateResponse */
        RateResponse: {
            /** Run Id */
            run_id: string;
            /** Rating */
            rating: string;
            /** Feedback Text */
            feedback_text: string | null;
        };
        /** RecommendationListResponse */
        RecommendationListResponse: {
            /** Items */
            items: components["schemas"]["RecommendationResponse"][];
            /** Next Cursor */
            next_cursor: string | null;
        };
        /** RecommendationResponse */
        RecommendationResponse: {
            /** Id */
            id: string;
            /** Audit Id */
            audit_id: string;
            /** Category */
            category: string;
            /** Priority */
            priority: number;
            /** Title */
            title: string;
            /** Why */
            why: string;
            /** Action Label */
            action_label: string;
            /** Action Route */
            action_route: string;
            /** Action Tool Id */
            action_tool_id: string | null;
            /** Estimated Impact Points */
            estimated_impact_points: number;
            /** Status */
            status: string;
            /** Completed At */
            completed_at: string | null;
        };
        /** RecommendationUpdateRequest */
        RecommendationUpdateRequest: {
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "in_progress" | "done" | "dismissed";
        };
        /** RecurringSlotsRequest */
        RecurringSlotsRequest: {
            cadence: components["schemas"]["Cadence"];
        };
        /** RefreshResponse */
        RefreshResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
            /** Expires In */
            expires_in: number;
        };
        /** RegenerateRequest */
        RegenerateRequest: {
            /** Nudge */
            nudge?: string | null;
        };
        /** RegisterRequest */
        RegisterRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
            /** Full Name */
            full_name: string;
        };
        /** ReminderRequest */
        ReminderRequest: {
            /** Reminder At */
            reminder_at?: string | null;
        };
        /** RenameConversationRequest */
        RenameConversationRequest: {
            /** Title */
            title: string;
        };
        /** RescheduleRequest */
        RescheduleRequest: {
            /**
             * Planned For
             * Format: date
             */
            planned_for: string;
            /** Planned Time */
            planned_time?: string | null;
        };
        /** ResendVerificationRequest */
        ResendVerificationRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
        };
        /** ResetPasswordRequest */
        ResetPasswordRequest: {
            /** Token */
            token: string;
            /** New Password */
            new_password: string;
        };
        /** ResumeAward */
        ResumeAward: {
            /** Name */
            name?: string | null;
            /** Issuer */
            issuer?: string | null;
            date?: components["schemas"]["DatePart"] | null;
            /** Description */
            description?: string | null;
        };
        /** ResumeCertification */
        ResumeCertification: {
            /** Name */
            name?: string | null;
            /** Issuer */
            issuer?: string | null;
            issued?: components["schemas"]["DatePart"] | null;
            /** Credential Id */
            credential_id?: string | null;
            /** Url */
            url?: string | null;
        };
        /** ResumeContact */
        ResumeContact: {
            /** Full Name */
            full_name?: string | null;
            /** Email */
            email?: string | null;
            /** Phone */
            phone?: string | null;
            /** Location */
            location?: string | null;
            /** Linkedin Url */
            linkedin_url?: string | null;
            /** Website Url */
            website_url?: string | null;
        };
        /** ResumeCustomSection */
        ResumeCustomSection: {
            /** Heading */
            heading: string;
            /** Bullets */
            bullets?: string[];
        };
        /**
         * ResumeDocument
         * @description The one canonical shape every resume input path must converge on.
         */
        ResumeDocument: {
            /**
             * Version
             * @default 1
             */
            version: number;
            source: components["schemas"]["ResumeSource"];
            contact?: components["schemas"]["ResumeContact"] | null;
            /** Summary */
            summary?: string | null;
            /** Experiences */
            experiences?: components["schemas"]["ResumeExperience"][];
            /** Education */
            education?: components["schemas"]["ResumeEducation"][];
            skills?: components["schemas"]["ResumeSkills"] | null;
            /** Certifications */
            certifications?: components["schemas"]["ResumeCertification"][];
            /** Projects */
            projects?: components["schemas"]["ResumeProject"][];
            /** Awards */
            awards?: components["schemas"]["ResumeAward"][];
            /** Publications */
            publications?: components["schemas"]["ResumePublication"][];
            /** Custom Sections */
            custom_sections?: components["schemas"]["ResumeCustomSection"][];
            /** Field Provenance */
            field_provenance?: {
                [key: string]: components["schemas"]["ResumeFieldProvenance"];
            };
        };
        /** ResumeEducation */
        ResumeEducation: {
            /** School */
            school?: string | null;
            /** Degree */
            degree?: string | null;
            /** Field */
            field?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
            /** Description */
            description?: string | null;
        };
        /** ResumeExperience */
        ResumeExperience: {
            /** Company */
            company?: string | null;
            /** Title */
            title?: string | null;
            /** Location */
            location?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
            /** Is Current */
            is_current?: boolean | null;
            /** Bullets */
            bullets?: string[];
            /** Technologies */
            technologies?: string[];
        };
        /** ResumeFieldProvenance */
        ResumeFieldProvenance: {
            source: components["schemas"]["ProvenanceSource"];
            /** Confidence */
            confidence: number;
        };
        /** ResumeMatchResponse */
        ResumeMatchResponse: {
            /** Id */
            id: string;
            /** Resume Id */
            resume_id: string;
            /** Job Description Id */
            job_description_id: string;
            /** Overall Match */
            overall_match: number;
            /** Component Scores */
            component_scores: unknown[];
            /** Matched */
            matched: unknown[];
            /** Missing */
            missing: unknown[];
            /** Transferable */
            transferable: unknown[];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * ResumeParseResponse
         * @description Returned by the paste/upload parse endpoints -- always a draft
         *     for the user to review and correct, never yet committed.
         */
        ResumeParseResponse: {
            draft: components["schemas"]["ResumeDocument"];
            /** Warnings */
            warnings: string[];
        };
        /** ResumeProject */
        ResumeProject: {
            /** Name */
            name?: string | null;
            /** Description */
            description?: string | null;
            /** Url */
            url?: string | null;
            /** Technologies */
            technologies?: string[];
        };
        /** ResumePublication */
        ResumePublication: {
            /** Title */
            title?: string | null;
            /** Publisher */
            publisher?: string | null;
            date?: components["schemas"]["DatePart"] | null;
            /** Url */
            url?: string | null;
            /** Description */
            description?: string | null;
        };
        /** ResumeResponse */
        ResumeResponse: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            /** Source */
            source: string;
            parsed: components["schemas"]["ResumeDocument"];
            /** Version */
            version: number;
            /** Is Active */
            is_active: boolean;
            /** Ats Score */
            ats_score: number | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ResumeSkills */
        ResumeSkills: {
            /** Technical */
            technical?: string[];
            /** Tools */
            tools?: string[];
            /** Soft */
            soft?: string[];
        };
        /**
         * ResumeSource
         * @enum {string}
         */
        ResumeSource: "upload" | "built" | "imported_from_profile";
        /** ReviewFlagRequest */
        ReviewFlagRequest: {
            /** Status */
            status: string;
            /** Note */
            note?: string | null;
        };
        /** SaveAssetRequest */
        SaveAssetRequest: {
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Folder Id */
            folder_id?: string | null;
        };
        /** SaveCarouselRequest */
        SaveCarouselRequest: {
            /** Title */
            title: string;
            data: components["schemas"]["CarouselData"];
        };
        /** SaveConversationRequest */
        SaveConversationRequest: {
            /** Title */
            title?: string | null;
        };
        /** ScoreComponentResponse */
        ScoreComponentResponse: {
            /** Name */
            name: string;
            /** Weight */
            weight: number;
            /** Value */
            value: number | null;
            /** Evidence */
            evidence: {
                [key: string]: unknown;
            };
        };
        /** ScoreDeltaResponse */
        ScoreDeltaResponse: {
            /** Score Type */
            score_type: string;
            /** From Value */
            from_value: number | null;
            /** To Value */
            to_value: number | null;
            /** Delta */
            delta: number | null;
        };
        /** ScoreHistoryPoint */
        ScoreHistoryPoint: {
            /** Audit Id */
            audit_id: string;
            /**
             * Recorded At
             * Format: date-time
             */
            recorded_at: string;
            /** Overall */
            overall: number;
            /** Profile */
            profile: number | null;
            /** Content */
            content: number | null;
            /** Engagement */
            engagement: number | null;
            /** Career */
            career: number | null;
            /** Visibility */
            visibility: number | null;
        };
        /** ScoreHistoryPointResponse */
        ScoreHistoryPointResponse: {
            /**
             * Snapshot Date
             * Format: date
             */
            snapshot_date: string;
            /** Value */
            value: number;
        };
        /** ScoreHistoryResponse */
        ScoreHistoryResponse: {
            /** Range */
            range: string;
            /** Points */
            points: components["schemas"]["ScoreHistoryPoint"][];
        };
        /** SendMessageRequest */
        SendMessageRequest: {
            /** Text */
            text: string;
        };
        /** SendMessageResponse */
        SendMessageResponse: {
            message: components["schemas"]["AssistantMessageResponse"];
            quota: components["schemas"]["QuotaInfo"];
            /** Quota Warning */
            quota_warning?: string | null;
        };
        /** SessionOut */
        SessionOut: {
            /** Id */
            id: string;
            /** User Agent */
            user_agent: string | null;
            /**
             * Issued At
             * Format: date-time
             */
            issued_at: string;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Current */
            current: boolean;
        };
        /** SetFlagGlobalRequest */
        SetFlagGlobalRequest: {
            /** Enabled Globally */
            enabled_globally: boolean;
        };
        /** SetFlagRolloutRequest */
        SetFlagRolloutRequest: {
            /** Rollout Percent */
            rollout_percent: number;
        };
        /** SetFlagUserOverrideRequest */
        SetFlagUserOverrideRequest: {
            /** User Id */
            user_id: string;
            /** Enabled */
            enabled: boolean | null;
        };
        /** SetPreferenceRequest */
        SetPreferenceRequest: {
            /**
             * Channel
             * @enum {string}
             */
            channel: "in_app" | "email";
            /** Type */
            type: string;
            /** Enabled */
            enabled: boolean;
        };
        /** Skill */
        Skill: {
            /** Name */
            name?: string | null;
            /** Endorsements */
            endorsements?: number | null;
            /** Is Top */
            is_top?: boolean | null;
        };
        /** SlowPromptResponse */
        SlowPromptResponse: {
            /** Prompt Id */
            prompt_id: string;
            /** Avg Latency Ms */
            avg_latency_ms: number;
            /** P95 Latency Ms */
            p95_latency_ms: number;
            /** Invocation Count */
            invocation_count: number;
        };
        /** SnapshotDetail */
        SnapshotDetail: {
            /** Version */
            version: number;
            /** Source */
            source: string;
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            /** Completeness Score */
            completeness_score: number | null;
            /** Is Active */
            is_active: boolean;
            payload: components["schemas"]["ProfileSnapshot"];
        };
        /** SnapshotDiff */
        SnapshotDiff: {
            /** From Version */
            from_version: number;
            /** To Version */
            to_version: number;
            /** Field Changes */
            field_changes: components["schemas"]["FieldChange"][];
            /** List Changes */
            list_changes: {
                [key: string]: components["schemas"]["ListItemChange"][];
            };
        };
        /**
         * SnapshotSummary
         * @description One row of `GET /api/v1/profile/snapshots` — no payload, just enough
         *     to list and pick a version.
         */
        SnapshotSummary: {
            /** Version */
            version: number;
            /** Source */
            source: string;
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            /** Completeness Score */
            completeness_score: number | null;
            /** Is Active */
            is_active: boolean;
        };
        /** SubscriptionResponse */
        SubscriptionResponse: {
            /** Id */
            id: string;
            /** Provider */
            provider: string;
            /**
             * Plan
             * @enum {string}
             */
            plan: "free" | "pro";
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "year";
            /** Status */
            status: string;
            /** Current Period Start */
            current_period_start: string | null;
            /** Current Period End */
            current_period_end: string | null;
            /** Cancel At Period End */
            cancel_at_period_end: boolean;
            /** Trial Ends At */
            trial_ends_at: string | null;
            /** Currency */
            currency: string;
            /** Amount Minor */
            amount_minor: number;
        };
        /** SuggestedPromptsResponse */
        SuggestedPromptsResponse: {
            /** Prompts */
            prompts: string[];
        };
        /** SuspendUserRequest */
        SuspendUserRequest: {
            /** Reason */
            reason: string;
        };
        /** SyncResponse */
        SyncResponse: {
            draft: components["schemas"]["ProfileSnapshot"];
            /** Available Fields */
            available_fields: string[];
        };
        /** ToolRunRequest */
        ToolRunRequest: {
            /** Input */
            input: {
                [key: string]: unknown;
            };
        };
        /** ToolRunResponse */
        ToolRunResponse: {
            /** Run Id */
            run_id: string;
            /** Output */
            output: {
                [key: string]: unknown;
            };
            /** Context Used */
            context_used: string[];
            quota: components["schemas"]["QuotaInfo"];
            /** Warning */
            warning?: string | null;
        };
        /**
         * ToolRunSummary
         * @description One row of `GET /api/v1/tools/{id}/runs`.
         */
        ToolRunSummary: {
            /** Id */
            id: string;
            /** Tool Id */
            tool_id: string;
            /** Input */
            input: {
                [key: string]: unknown;
            };
            /** Output */
            output: {
                [key: string]: unknown;
            } | null;
            /** Context Used */
            context_used: string[];
            /** Status */
            status: string;
            /** Rating */
            rating: string | null;
            /** Feedback Text */
            feedback_text: string | null;
            /** Parent Run Id */
            parent_run_id: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * ToolSummary
         * @description One row of `GET /api/v1/tools` -- everything the web app needs to
         *     render a tool card and, on selection, a fully working form and
         *     result view with no tool-specific frontend code.
         */
        ToolSummary: {
            /** Id */
            id: string;
            /** Hub */
            hub: string;
            /** Name */
            name: string;
            /** Short Description */
            short_description: string;
            /** Input Schema */
            input_schema: {
                [key: string]: unknown;
            };
            /** Output Schema */
            output_schema: {
                [key: string]: unknown;
            };
            /** Required Context */
            required_context: string[];
            /** Optional Context */
            optional_context: string[];
            /** Min Plan */
            min_plan: string;
            /** Quota Metric */
            quota_metric: string;
            /** Result Renderer */
            result_renderer: string;
            /** Save As */
            save_as: string | null;
            /** Free Daily Cap */
            free_daily_cap: number | null;
            /** Supports Streaming */
            supports_streaming: boolean;
            /** Counts As Outreach */
            counts_as_outreach: boolean;
        };
        /** UpdateProfileRequest */
        UpdateProfileRequest: {
            /** Full Name */
            full_name?: string | null;
            /** Locale */
            locale?: string | null;
            /** Timezone */
            timezone?: string | null;
        };
        /** UserPublic */
        UserPublic: {
            /** Id */
            id: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /** Avatar Url */
            avatar_url: string | null;
            /** Locale */
            locale: string;
            /** Timezone */
            timezone: string;
            /** Role */
            role: string;
            /** Plan */
            plan: string;
            /** Email Verified */
            email_verified: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** VerifyEmailRequest */
        VerifyEmailRequest: {
            /** Token */
            token: string;
        };
        /** VoiceDescriptorResponse */
        VoiceDescriptorResponse: {
            /**
             * Source
             * @enum {string}
             */
            source: "supplied" | "derived" | "default";
            /** Sample Count */
            sample_count: number;
            /** Tone Adjectives */
            tone_adjectives: string[];
            /** Recurring Themes */
            recurring_themes: string[];
            /** Signature Structures */
            signature_structures: string[];
            /** Vocabulary Preferences */
            vocabulary_preferences: string[];
            /** Never Does */
            never_does: string[];
        };
        /** VoiceSamplesRequest */
        VoiceSamplesRequest: {
            /** Texts */
            texts: string[];
        };
        /** WebhookEventResponse */
        WebhookEventResponse: {
            /** Id */
            id: string;
            /** Provider */
            provider: string;
            /** Provider Event Id */
            provider_event_id: string;
            /** Type */
            type: string;
            /** Status */
            status: string;
            /** Attempts */
            attempts: number;
            /**
             * Received At
             * Format: date-time
             */
            received_at: string;
            /** Processed At */
            processed_at: string | null;
            /** Error */
            error: string | null;
        };
        /** WeeklyPlanItemResponse */
        WeeklyPlanItemResponse: {
            /** Title */
            title: string;
            /** Why Now */
            why_now: string;
            /** Tool Id */
            tool_id: string | null;
            /** Estimated Minutes */
            estimated_minutes: number;
            /** Expected Impact */
            expected_impact: number;
            /** Category */
            category: string;
            /** Completed */
            completed: boolean;
        };
        /** WeeklyPlanItemUpdate */
        WeeklyPlanItemUpdate: {
            /** Completed */
            completed: boolean;
        };
        /** WeeklyPlanResponse */
        WeeklyPlanResponse: {
            /** Id */
            id: string;
            /**
             * Week Start
             * Format: date
             */
            week_start: string;
            /**
             * Generated At
             * Format: date-time
             */
            generated_at: string;
            /** Focus */
            focus: string;
            /** Items */
            items: components["schemas"]["WeeklyPlanItemResponse"][];
            /** Status */
            status: string;
            /** Completed Count */
            completed_count: number;
            /** Reflection */
            reflection: {
                [key: string]: unknown;
            } | null;
        };
        /** WorkspaceAssetResponse */
        WorkspaceAssetResponse: {
            /** Id */
            id: string;
            /** Type */
            type: string;
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Body Format */
            body_format: string;
            /** Metadata */
            metadata: {
                [key: string]: unknown;
            };
            /** Source Tool Run Id */
            source_tool_run_id: string | null;
            /** Tags */
            tags: string[];
            /** Is Favourite */
            is_favourite: boolean;
            /** Folder Id */
            folder_id: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Deleted At */
            deleted_at: string | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    register_api_v1_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    verify_email_api_v1_auth_verify_email_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyEmailRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    resend_verification_api_v1_auth_resend_verification_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResendVerificationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_api_v1_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_api_v1_auth_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RefreshResponse"];
                };
            };
        };
    };
    logout_api_v1_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
        };
    };
    logout_all_api_v1_auth_logout_all_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
        };
    };
    list_sessions_api_v1_auth_sessions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionOut"][];
                };
            };
        };
    };
    delete_session_api_v1_auth_sessions__session_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    forgot_password_api_v1_auth_forgot_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ForgotPasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reset_password_api_v1_auth_reset_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResetPasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_password_api_v1_auth_change_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangePasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    linkedin_start_api_v1_auth_linkedin_start_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LinkedInStartResponse"];
                };
            };
        };
    };
    linkedin_callback_api_v1_auth_linkedin_callback_get: {
        parameters: {
            query: {
                code: string;
                state: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_api_v1_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeResponse"];
                };
            };
        };
    };
    delete_me_api_v1_me_delete: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DeleteAccountRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_me_api_v1_me_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateProfileRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserPublic"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    request_data_export_api_v1_me_export_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExportJobResponse"];
                };
            };
        };
    };
    download_data_export_api_v1_me_export__export_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                export_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    connect_api_v1_profile_connect_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LinkedInStartResponse"];
                };
            };
        };
    };
    connect_callback_api_v1_profile_connect_callback_get: {
        parameters: {
            query: {
                code: string;
                state: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    sync_api_v1_profile_sync_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SyncResponse"];
                };
            };
        };
    };
    commit_sync_api_v1_profile_sync_commit_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommitImportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_paste_import_api_v1_profile_imports_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ImportPasteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_upload_import_api_v1_profile_imports_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_create_upload_import_api_v1_profile_imports_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    commit_import_api_v1_profile_imports__import_id__commit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                import_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommitImportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_current_snapshot_api_v1_profile_snapshot_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotDetail"];
                };
            };
        };
    };
    put_manual_snapshot_api_v1_profile_snapshot_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProfileSnapshot"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_snapshots_api_v1_profile_snapshots_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"][];
                };
            };
        };
    };
    get_snapshot_diff_api_v1_profile_snapshots__version_a__diff__version_b__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_a: number;
                version_b: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotDiff"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_gateway_metrics_internal_metrics_get: {
        parameters: {
            query?: {
                window_hours?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GatewayMetricsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_playground_prompts_internal_playground_prompts_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaygroundPromptSummary"][];
                };
            };
        };
    };
    run_playground_prompt_internal_playground_run_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaygroundRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaygroundRunResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    stream_playground_prompt_internal_playground_stream_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaygroundRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_job_status_api_v1_jobs__job_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobStatusResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_audit_api_v1_audits_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AuditRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditRunResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_latest_api_v1_audits_latest_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditDetailResponse"];
                };
            };
        };
    };
    get_audit_api_v1_audits__audit_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                audit_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_score_history_endpoint_api_v1_scores_history_get: {
        parameters: {
            query?: {
                range?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScoreHistoryResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_recommendations_api_v1_recommendations_get: {
        parameters: {
            query?: {
                status?: string | null;
                cursor?: number | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationListResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_recommendation_api_v1_recommendations__recommendation_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                recommendation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_dashboard_api_v1_dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DashboardResponse"];
                };
            };
        };
    };
    list_tools_api_v1_tools_get: {
        parameters: {
            query?: {
                hub?: components["schemas"]["Hub"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ToolSummary"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    run_tool_api_v1_tools__tool_id__run_post: {
        parameters: {
            query?: {
                stream?: boolean;
            };
            header?: never;
            path: {
                tool_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ToolRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_tool_runs_api_v1_tools__tool_id__runs_get: {
        parameters: {
            query?: {
                cursor?: string | null;
                limit?: number;
            };
            header?: never;
            path: {
                tool_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ToolRunSummary"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_tool_run_api_v1_tools_runs__run_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ToolRunSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    regenerate_tool_run_api_v1_tools_runs__run_id__regenerate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegenerateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ToolRunResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    rate_tool_run_api_v1_tools_runs__run_id__rate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_tool_run_api_v1_tools_runs__run_id__save_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveAssetRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_voice_profile_api_v1_content_voice_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VoiceDescriptorResponse"];
                };
            };
        };
    };
    submit_pasted_samples_api_v1_content_voice_samples_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VoiceSamplesRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VoiceDescriptorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_uploaded_samples_api_v1_content_voice_samples_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_submit_uploaded_samples_api_v1_content_voice_samples_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VoiceDescriptorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_assets_endpoint_api_v1_assets_get: {
        parameters: {
            query?: {
                type?: string | null;
                folder_id?: string | null;
                tags?: string[] | null;
                favourite?: boolean | null;
                date_from?: string | null;
                date_to?: string | null;
                source_tool_id?: string | null;
                q?: string | null;
                cursor?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetListResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_asset_endpoint_api_v1_assets_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateAssetRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_asset_posted_api_v1_assets__asset_id__mark_posted_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkPostedRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_carousel_endpoint_api_v1_carousels_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveCarouselRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CarouselResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_carousel_endpoint_api_v1_carousels__asset_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CarouselResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_carousel_endpoint_api_v1_carousels__asset_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveCarouselRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CarouselResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_carousel_pdf_endpoint_api_v1_carousels__asset_id__export_pdf_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_carousel_png_endpoint_api_v1_carousels__asset_id__export_png_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_plans_endpoint_api_v1_content_plans_get: {
        parameters: {
            query: {
                start: string;
                end: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_plan_endpoint_api_v1_content_plans_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ContentPlanCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    consistency_endpoint_api_v1_content_plans_consistency_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConsistencyWeek"][];
                };
            };
        };
    };
    performance_summary_endpoint_api_v1_content_plans_performance_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PerformanceSummaryResponse"];
                };
            };
        };
    };
    get_plan_endpoint_api_v1_content_plans__plan_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_plan_endpoint_api_v1_content_plans__plan_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_plan_endpoint_api_v1_content_plans__plan_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ContentPlanUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reschedule_plan_endpoint_api_v1_content_plans__plan_id__reschedule_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RescheduleRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_reminder_endpoint_api_v1_content_plans__plan_id__reminder_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReminderRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_posted_endpoint_api_v1_content_plans__plan_id__mark_posted_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkContentPlanPostedRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    record_performance_endpoint_api_v1_content_plans__plan_id__performance_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PerformanceNumbers"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    recurring_slots_endpoint_api_v1_content_plans_recurring_slots_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecurringSlotsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    bulk_schedule_endpoint_api_v1_content_plans_bulk_schedule_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BulkScheduleRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    parse_resume_paste_endpoint_api_v1_career_resumes_parse_paste_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: string;
                };
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeParseResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeParseResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    parse_resume_from_profile_endpoint_api_v1_career_resumes_from_profile_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeParseResponse"];
                };
            };
        };
    };
    list_resumes_endpoint_api_v1_career_resumes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"][];
                };
            };
        };
    };
    commit_resume_endpoint_api_v1_career_resumes_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommitResumeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_resume_endpoint_api_v1_career_resumes__resume_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_resume_endpoint_api_v1_career_resumes__resume_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activate_resume_endpoint_api_v1_career_resumes__resume_id__activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_resume_pdf_endpoint_api_v1_career_resumes__resume_id__export_pdf_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_resume_docx_endpoint_api_v1_career_resumes__resume_id__export_docx_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_job_descriptions_endpoint_api_v1_career_job_descriptions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobDescriptionResponse"][];
                };
            };
        };
    };
    create_job_description_endpoint_api_v1_career_job_descriptions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["JobDescriptionParseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobDescriptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_description_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobDescriptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_description_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_matches_endpoint_api_v1_career_matches_get: {
        parameters: {
            query?: {
                resume_id?: string | null;
                job_description_id?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeMatchResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_match_endpoint_api_v1_career_matches_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateResumeMatchRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeMatchResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_scores_endpoint_api_v1_growth_scores_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GrowthScoresResponse"];
                };
            };
        };
    };
    get_current_plan_endpoint_api_v1_growth_plan_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WeeklyPlanResponse"];
                };
            };
        };
    };
    update_plan_item_endpoint_api_v1_growth_plan__plan_id__items__item_index__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
                item_index: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WeeklyPlanItemUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WeeklyPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_active_goal_endpoint_api_v1_growth_goal_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GrowthGoalResponse"];
                };
            };
        };
    };
    start_goal_endpoint_api_v1_growth_goal_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GrowthGoalCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GrowthGoalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_coach_conversation_endpoint_api_v1_growth_coach_conversation_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationSummary"];
                };
            };
        };
    };
    send_coach_message_endpoint_api_v1_growth_coach_messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SendMessageRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantMessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_score_history_endpoint_api_v1_growth_scores_history_get: {
        parameters: {
            query?: {
                months?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GrowthScoreHistoryResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_before_after_endpoint_api_v1_growth_before_after_get: {
        parameters: {
            query: {
                from_date: string;
                to_date: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BeforeAfterResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_trash_endpoint_api_v1_assets_trash_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceAssetResponse"][];
                };
            };
        };
    };
    get_asset_endpoint_api_v1_assets__asset_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceAssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_asset_endpoint_api_v1_assets__asset_id__delete: {
        parameters: {
            query?: {
                permanent?: boolean;
            };
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    patch_asset_endpoint_api_v1_assets__asset_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssetPatchRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceAssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    restore_asset_endpoint_api_v1_assets__asset_id__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceAssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    duplicate_asset_endpoint_api_v1_assets__asset_id__duplicate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceAssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_versions_endpoint_api_v1_assets__asset_id__versions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetVersionResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_asset_endpoint_api_v1_assets__asset_id__export_get: {
        parameters: {
            query?: {
                format?: string;
            };
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    bulk_action_endpoint_api_v1_assets_bulk_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BulkActionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BulkActionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_folders_endpoint_api_v1_asset_folders_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetFolderResponse"][];
                };
            };
        };
    };
    create_folder_endpoint_api_v1_asset_folders_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssetFolderCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetFolderResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_folder_endpoint_api_v1_asset_folders__folder_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                folder_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_folder_endpoint_api_v1_asset_folders__folder_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                folder_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssetFolderUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetFolderResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_suggested_prompts_api_v1_assistant_suggested_prompts_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SuggestedPromptsResponse"];
                };
            };
        };
    };
    list_conversations_endpoint_api_v1_assistant_conversations_get: {
        parameters: {
            query?: {
                q?: string | null;
                include_archived?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationSummary"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_conversation_endpoint_api_v1_assistant_conversations_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConversationCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_conversation_endpoint_api_v1_assistant_conversations__conversation_id__get: {
        parameters: {
            query?: {
                leaf_message_id?: string | null;
                /** @description Return every branch, not just the active thread */
                all_branches?: boolean;
            };
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_conversation_endpoint_api_v1_assistant_conversations__conversation_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    rename_conversation_endpoint_api_v1_assistant_conversations__conversation_id__rename_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RenameConversationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    archive_conversation_endpoint_api_v1_assistant_conversations__conversation_id__archive_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ArchiveConversationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_conversation_endpoint_api_v1_assistant_conversations__conversation_id__save_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveConversationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_context_settings_endpoint_api_v1_assistant_conversations__conversation_id__context_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContextSettingsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_context_settings_endpoint_api_v1_assistant_conversations__conversation_id__context_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ContextTogglesRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContextSettingsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    send_message_endpoint_api_v1_assistant_conversations__conversation_id__messages_post: {
        parameters: {
            query?: {
                stream?: boolean;
            };
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SendMessageRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    retry_message_endpoint_api_v1_assistant_conversations__conversation_id__messages__message_id__retry_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
                message_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SendMessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    edit_message_endpoint_api_v1_assistant_conversations__conversation_id__messages__message_id__edit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
                message_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EditMessageRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SendMessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    rate_message_endpoint_api_v1_assistant_conversations__conversation_id__messages__message_id__rate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
                message_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RateMessageRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantMessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    confirm_tool_endpoint_api_v1_assistant_conversations__conversation_id__confirm_tool_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConfirmToolRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantMessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_pricing_api_v1_billing_pricing_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PricingResponse"];
                };
            };
        };
    };
    get_subscription_api_v1_billing_subscription_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscriptionResponse"];
                };
            };
        };
    };
    list_payments_api_v1_billing_payments_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaymentResponse"][];
                };
            };
        };
    };
    create_checkout_api_v1_billing_checkout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CheckoutRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CheckoutResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_portal_api_v1_billing_portal_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PortalResponse"];
                };
            };
        };
    };
    cancel_subscription_api_v1_billing_cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CancelSubscriptionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscriptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_plan_api_v1_billing_change_plan_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangePlanRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscriptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    stripe_webhook_api_v1_billing_webhooks_stripe_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
    razorpay_webhook_api_v1_billing_webhooks_razorpay_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
    list_notifications_endpoint_api_v1_notifications_get: {
        parameters: {
            query?: {
                unread_only?: boolean;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotificationListResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_read_endpoint_api_v1_notifications__notification_id__read_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                notification_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_all_read_endpoint_api_v1_notifications_read_all_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    get_preferences_endpoint_api_v1_notifications_preferences_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PreferencesResponse"];
                };
            };
        };
    };
    set_preference_endpoint_api_v1_notifications_preferences_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SetPreferenceRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PreferencesResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unsubscribe_get_api_v1_notifications_unsubscribe_get: {
        parameters: {
            query: {
                token: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/html": string;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unsubscribe_post_api_v1_notifications_unsubscribe_post: {
        parameters: {
            query: {
                token: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/html": string;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    search_users_endpoint_api_v1_admin_users_get: {
        parameters: {
            query?: {
                q?: string | null;
                plan?: string | null;
                status?: string | null;
                signed_up_after?: string | null;
                signed_up_before?: string | null;
                offset?: number;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserSearchResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_user_detail_endpoint_api_v1_admin_users__user_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    suspend_user_endpoint_api_v1_admin_users__user_id__suspend_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SuspendUserRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reinstate_user_endpoint_api_v1_admin_users__user_id__reinstate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    force_password_reset_endpoint_api_v1_admin_users__user_id__force_password_reset_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ForcePasswordResetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    adjust_plan_endpoint_api_v1_admin_users__user_id__adjust_plan_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdjustPlanRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminUserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    impersonate_user_endpoint_api_v1_admin_users__user_id__impersonate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImpersonateResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_subscriptions_endpoint_api_v1_admin_subscriptions_get: {
        parameters: {
            query?: {
                status?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminSubscriptionResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_webhook_history_endpoint_api_v1_admin_subscriptions__subscription_id__webhooks_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                subscription_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WebhookEventResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    replay_webhook_endpoint_api_v1_admin_webhooks__webhook_event_id__replay_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                webhook_event_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WebhookEventResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_feature_flags_endpoint_api_v1_admin_feature_flags_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeatureFlagResponse"][];
                };
            };
        };
    };
    set_flag_global_endpoint_api_v1_admin_feature_flags__key__global_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                key: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SetFlagGlobalRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeatureFlagResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_flag_rollout_endpoint_api_v1_admin_feature_flags__key__rollout_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                key: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SetFlagRolloutRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeatureFlagResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_flag_user_override_endpoint_api_v1_admin_feature_flags__key__user_override_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                key: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SetFlagUserOverrideRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ai_ops_overview_endpoint_api_v1_admin_ai_ops_overview_get: {
        parameters: {
            query?: {
                days?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AiOpsOverviewResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    prompt_drilldown_endpoint_api_v1_admin_ai_ops_prompts__prompt_id__get: {
        parameters: {
            query?: {
                days?: number;
            };
            header?: never;
            path: {
                prompt_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AiInvocationResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_moderation_flags_endpoint_api_v1_admin_moderation_flags_get: {
        parameters: {
            query?: {
                status?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModerationFlagResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    review_moderation_flag_endpoint_api_v1_admin_moderation_flags__flag_id__review_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                flag_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReviewFlagRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModerationFlagResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    platform_health_endpoint_api_v1_admin_platform_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlatformHealthResponse"];
                };
            };
        };
    };
    retry_dead_job_endpoint_api_v1_admin_jobs__job_id__retry_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
    ready_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
}
