import * as constants from '../../constants/constants';


const TEST_ENDPOINTS = {
    'TASK_CREATE_ENDPOINT': '/api/create-task',
    'TASK_UPDATE_ENDPOINT': '/api/update-task',
    'TASK_DELETE_ENDPOINT': '/api/delete-task',
    'TASK_STATUS_UPDATE_ENDPOINT': '/api/update-task-status',
    'TASKS_LIST_ENDPOINT': '/api/tasks',
};

describe('verify endpoints are correct', () => {
    test('task create endpoint is the expected value.', () => {
        expect(constants.ENDPOINTS.TASK_CREATE_ENDPOINT).toBe(
            TEST_ENDPOINTS.TASK_CREATE_ENDPOINT
        );
    });

    test('task update endpoint is the expected value.', () => {
        expect(constants.ENDPOINTS.TASK_UPDATE_ENDPOINT).toBe(
            TEST_ENDPOINTS.TASK_UPDATE_ENDPOINT
        );
    });

    test('task delete endpoint is the expected value.', () => {
        expect(constants.ENDPOINTS.TASK_DELETE_ENDPOINT).toBe(
            TEST_ENDPOINTS.TASK_DELETE_ENDPOINT
        );
    });

    test('task status update endpoint is the expected value.', () => {
        expect(constants.ENDPOINTS.TASK_STATUS_UPDATE_ENDPOINT).toBe(
            TEST_ENDPOINTS.TASK_STATUS_UPDATE_ENDPOINT
        );
    });

    test('tasks endpoint is the expected value.', () => {
        expect(constants.ENDPOINTS.TASKS_LIST_ENDPOINT).toBe(
            TEST_ENDPOINTS.TASKS_LIST_ENDPOINT
        );
    });
});


test('task unexpected error message endpoint is the expected value.', () => {
    expect(constants.UNEXPECTED_ERROR_MESSAGE).toBe(
        'An unexpected error occurred. Please try again.'
    );
});
