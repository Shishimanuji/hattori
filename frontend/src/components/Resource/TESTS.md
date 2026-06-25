# Resource Management Component Tests

This document describes the comprehensive test suite for the Resource Management Frontend components.

## Test Files

### 1. ResourceList.test.tsx.skip

**Component Tested**: `ResourceList`

**Test Coverage**:
- ✅ Renders resource list with data from API
- ✅ Filters resources by search term
- ✅ Displays correct status badges (Active/Inactive)
- ✅ Calls `onEdit` callback when edit button clicked
- ✅ Shows confirmation dialog on delete
- ✅ Calls `onDelete` callback after confirming deletion
- ✅ Displays empty state when no resources available
- ✅ Pagination controls work correctly
- ✅ Filters by asset type dropdown
- ✅ Filters by status dropdown
- ✅ Clear filters button resets all filters
- ✅ Currency formatting displays correctly
- ✅ Date formatting displays correctly

**Key Assertions**:
- Resource list renders with correct number of items
- Status badges have appropriate CSS classes
- Edit/Delete/View buttons have correct handlers
- Search input updates correctly
- Filter dropdowns change component behavior
- Empty state displays when appropriate

---

### 2. ResourceForm.test.tsx.skip

**Component Tested**: `ResourceForm`

**Test Coverage**:
- ✅ Renders all required form fields on mount
- ✅ Loads asset types from API on mount
- ✅ Validates required fields before submission
- ✅ Shows specific error messages for each field
- ✅ Loads custom fields when asset type is selected
- ✅ Submits form with valid data
- ✅ Calls `onSuccess` callback after successful submission
- ✅ Calls `onCancel` when cancel button clicked
- ✅ Handles API errors gracefully
- ✅ Disables form while submitting
- ✅ Pre-fills form in edit mode

**Tested Fields**:
- Resource Name (required)
- Asset Type (required)
- Cost (required, > 0)
- Allocation Date (required)
- Status (Active/Inactive)
- Custom fields (validated based on schema)

**Key Assertions**:
- Form validates all required fields
- Asset type selection triggers schema load
- Error messages display for invalid inputs
- Form submission calls mutation with correct data
- Edit mode loads existing resource data
- Custom field inputs render based on field type

---

### 3. AllocationControls.test.tsx.skip

**Component Tested**: `AllocationControls`

**Test Coverage**:
- ✅ Renders budget overview section
- ✅ Displays "Budget Available" message at <80% utilization
- ✅ Displays "Budget Warning" message at 80-99% utilization
- ✅ Displays "At Budget Limit" message at 100% utilization
- ✅ Calculates and displays correct utilization percentage
- ✅ Shows allocated, remaining, and total budget amounts
- ✅ Renders budget progress bar with correct color
- ✅ Color codes progress bar: green (<80%), yellow (80-99%), red (100%+)
- ✅ Shows deallocation form when button clicked
- ✅ Validates deallocation amount against allocated budget
- ✅ Displays quick reference section with budget summary
- ✅ Handles zero budget correctly
- ✅ Handles negative remaining budget (displays as $0)

**Status Indicator Tests**:
- Green checkmark + "Budget Available" at 25% utilization
- Yellow triangle + "Budget Warning" at 85% utilization
- Red circle + "At Budget Limit" at 100% utilization

**Key Assertions**:
- Utilization percentage calculated correctly
- Budget progress bar width matches utilization
- Status indicator color matches utilization level
- Warning/error messages display at correct thresholds
- Deallocation controls render correctly
- Quick reference displays all budget metrics

---

## Running the Tests

To run these tests, first install testing dependencies:

```bash
npm install --save-dev vitest @testing-library/react @testing-library/user-event @testing-library/dom
```

Then run tests:

```bash
# Run all tests
npm run test

# Run specific test file
npm run test -- ResourceList.test.tsx

# Run with coverage
npm run test -- --coverage

# Run in watch mode
npm run test -- --watch
```

## Test Patterns Used

### 1. Service Mocking
All API services are mocked using `vi.mock()` to test components in isolation:

```typescript
vi.mock('../../services/resources', () => ({
  resourceService: {
    getResources: vi.fn(),
    deleteResource: vi.fn(),
  },
}))
```

### 2. QueryClient Setup
Each test creates a fresh `QueryClient` to ensure test isolation:

```typescript
let queryClient: QueryClient

beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
})
```

### 3. Component Rendering
Components are wrapped with `QueryClientProvider`:

```typescript
render(
  <QueryClientProvider client={queryClient}>
    <ResourceList projectId="proj-1" onEdit={onEdit} />
  </QueryClientProvider>
)
```

### 4. Async Waiting
Tests use `waitFor()` to handle async operations:

```typescript
await waitFor(() => {
  expect(screen.getByText('Resource 1')).toBeInTheDocument()
})
```

### 5. User Interaction Testing
Tests simulate user actions:

```typescript
fireEvent.change(searchInput, { target: { value: 'search term' } })
fireEvent.click(editButton)
```

## Test Data

### Mock Resources
```typescript
{
  id: 'res-1',
  project_id: 'proj-1',
  asset_type_id: 'at-1',
  name: 'Resource 1',
  cost: 1000,
  allocation_date: '2024-01-15',
  status: 'Active',
  custom_fields: {},
  created_by: 'user-1',
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z',
}
```

### Mock Asset Types
```typescript
{
  id: 'at-1',
  name: 'Personnel',
  description: 'Personnel resources',
  is_active: true,
  custom_fields: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}
```

## Edge Cases Tested

### ResourceList
- Empty resource list
- Resources with various statuses
- Large result sets (pagination)
- Search with no matches
- Filter combinations

### ResourceForm
- Form submission with required fields only
- Custom field validation
- Asset type selection behavior
- Error display for invalid data
- Form pre-filling in edit mode

### AllocationControls
- Zero budget
- Negative remaining budget
- 100% allocation
- Boundary conditions (80%, 99%, 100%)
- Currency formatting edge cases

## Assertions

### Render Assertions
```typescript
expect(screen.getByText('Resource 1')).toBeInTheDocument()
expect(screen.getByLabelText(/Resource Name/)).toBeInTheDocument()
```

### Interaction Assertions
```typescript
expect(onEdit).toHaveBeenCalledWith('res-1')
expect(createResourceSpy).toHaveBeenCalled()
```

### UI State Assertions
```typescript
expect(submitButton).toHaveAttribute('disabled')
expect(statusBadge).toHaveClass('bg-green-100')
```

## Future Test Enhancements

- [ ] Add snapshot testing for component structure
- [ ] Add performance testing for large lists
- [ ] Add accessibility testing with jest-axe
- [ ] Add integration tests with real backend
- [ ] Add e2e tests with Playwright
- [ ] Add visual regression testing

## Notes

- Tests are currently marked with `.test.tsx.skip` to exclude them from TypeScript compilation in the build
- When testing dependencies are installed, rename files to `.test.tsx` to enable tests
- All tests follow AAA pattern: Arrange, Act, Assert
- Tests are isolated and can run in any order
- Mock data matches actual API response structure
