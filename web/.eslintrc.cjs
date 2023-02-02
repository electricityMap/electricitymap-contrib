module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2021: true,
  },
  parser: '@typescript-eslint/parser',
  plugins: ['react-prefer-function-component'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'plugin:react/recommended',
    'plugin:jsx-a11y/recommended',
    'plugin:react/jsx-runtime',
    'plugin:unicorn/recommended',
    'plugin:react-prefer-function-component/recommended',
    'prettier',
  ],
  rules: {
    // TODO: TEMPORARILY DISABLED DURING INITIAL DEVELOPMENT
    '@typescript-eslint/no-empty-interface': 'off',
    '@typescript-eslint/no-empty-function': 'off',

    curly: 'error',
    'no-promise-executor-return': 'error',
    'no-unreachable-loop': 'error',
    'require-atomic-updates': 'error',
    'default-case-last': 'error',
    'grouped-accessor-pairs': 'error',
    'no-constructor-return': 'error',
    'no-implicit-coercion': 'error',
    'prefer-regex-literals': 'error',
    'no-restricted-syntax': [
      'error',
      {
        selector: 'ForInStatement',
        message:
          'for..in loops iterate over the entire prototype chain, which is virtually never what you want. Use Object.{keys,values,entries}, and iterate over the resulting array.',
      },
      {
        selector: 'LabeledStatement',
        message:
          'Labels are a form of GOTO; using them makes code confusing and hard to maintain and understand.',
      },
      {
        selector: 'WithStatement',
        message:
          '`with` is disallowed in strict mode because it makes code impossible to predict and optimize.',
      },
    ],
    'no-void': 'off',
    '@typescript-eslint/no-unused-vars': [
      'warn', // TODO: Change to error when ready for production
      { args: 'after-used', argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
    '@typescript-eslint/ban-ts-comment': [
      'error',
      {
        'ts-expect-error': 'allow-with-description',
        'ts-ignore': 'allow-with-description',
      },
    ],
    '@typescript-eslint/no-confusing-void-expression': [
      'error',
      { ignoreArrowShorthand: true },
    ],
    'import/no-deprecated': 'error',
    'import/no-unresolved': 'off', // Off as TS handles this
    'import/no-extraneous-dependencies': [
      'error',
      {
        devDependencies: [
          'cypress.config.ts',
          'vite.config.ts',
          'src/testing/setupTests.ts',
          'src/testing/testUtils.tsx',
          'src/testing/mocks/**',
          'src/**/*.test.{ts,tsx}',
        ],
      },
    ],

    // Commented out as I don't think they were running anyway?
    // "react/no-string-refs": "off",
    // "react/no-this-in-sfc": "off",
    // "react/no-will-update-set-state": "off",
    // "react/prefer-es6-class": "off",
    // "react/no-unused-state": "off",
    // "react/prefer-stateless-function": "off",
    // "react/sort-comp": "off",
    // "react/state-in-constructor": "off",
    // "react/static-property-placement": "off",
    'react/prop-types': 'off',
    'react/boolean-prop-naming': [
      'error',
      {
        validateNested: true,
      },
    ],
    'react/function-component-definition': [
      'error',
      {
        namedComponents: 'function-declaration',
      },
    ],
    'react/no-unstable-nested-components': 'error',
    'react/jsx-handler-names': [
      'warn', // TODO: Change to error when ready for production
      {
        eventHandlerPrefix: 'handle',
        eventHandlerPropPrefix: 'on',
      },
    ],
    'react/jsx-no-bind': [
      'error',
      {
        ignoreRefs: false,
        allowArrowFunctions: true,
        allowFunctions: true,
        allowBind: false,
        ignoreDOMComponents: false,
      },
    ],
    'react/jsx-no-constructed-context-values': 'error',
    'react/jsx-no-script-url': 'error',
    'react/jsx-no-useless-fragment': 'error',

    'unicorn/filename-case': [
      'error',
      {
        cases: {
          camelCase: true,
          pascalCase: true,
        },
        ignore: ['FAQ'],
      },
    ],
    'unicorn/prevent-abbreviations': [
      'error',
      {
        ignore: ['.*[pP]rops'],
      },
    ],
    'unicorn/no-nested-ternary': ['error'],
    'unicorn/no-useless-undefined': 'off',
    'unicorn/no-null': 'off',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  overrides: [
    {
      files: ['src/**/*.ts?(x)'],
      parserOptions: {
        project: ['./tsconfig.json'],
      },
    },
    {
      files: [
        'vite.config.ts',
        'cypress.config.ts',
        'scripts/**/*.{mjs,js,ts}',
        'geo/*.ts',
      ],
      rules: {
        'unicorn/no-process-exit': 'off',
        'import/no-extraneous-dependencies': 'off',
        'unicorn/no-array-reduce': 'off',
      },
      parserOptions: {
        project: ['./tsconfig.node.json'],
      },
    },
    {
      files: ['src/**/*.stories.ts?(x)'],
      rules: {
        'import/no-extraneous-dependencies': 'off',
      },
    },
    {
      files: ['src/**/*.test.ts?(x)'],
      extends: ['plugin:testing-library/react'],
      rules: {
        '@typescript-eslint/no-magic-numbers': ['off'],
        'import/default': 'off',
        'testing-library/no-await-sync-events': [
          'error',
          {
            eventModules: ['fire-event'],
          },
        ],
        'testing-library/no-manual-cleanup': 'error',
        'testing-library/prefer-explicit-assert': 'error',
        'testing-library/prefer-user-event': 'error',
        'testing-library/prefer-wait-for': 'error',
      },
    },
  ],
};
