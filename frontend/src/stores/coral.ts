import { Survey } from "../types/survey";
import { defineStore } from "pinia";

export interface CoralData {
    selectedSurvey: Survey
}

export const useCoralDataStore =
    defineStore("coralData", {
        state: () => ({
            selectedSurvey : {} as Survey,
        }),

        actions: {
            selectSurvey(newSelected: Survey) {
                this.selectedSurvey = newSelected;
            },
            getSelectedSurveyId(): string {
                return this.selectedSurvey.id;
            },
        },
    });